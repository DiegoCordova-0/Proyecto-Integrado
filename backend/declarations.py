import csv
import io
from datetime import date
from decimal import Decimal
from typing import Any

from .database import obtener_conexion
from .calculator import (
    FACTOR_FINAL,
    FACTOR_INICIAL,
    calcular_factores_desde_montos,
    truncar_8_decimales,
    validar_factores_8_a_19,
)
from .mongo_db import registrar_log_auditoria


ESTADOS_DECLARACION = ("Borrador", "Pendiente", "Aprobado", "Rechazado")
FACTORES = tuple(f"factor_{i}" for i in range(FACTOR_INICIAL, FACTOR_FINAL + 1))
MONTOS = tuple(f"monto_{i}" for i in range(FACTOR_INICIAL, FACTOR_FINAL + 1))
LLAVE_CALIFICACION = ("corredor_id", "ejercicio", "mercado", "instrumento", "secuencia", "fecha_pago")


def validate_csv_text_cell(value: str | None) -> str | None:
    if value is None:
        return None
    if value.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")):
        raise ValueError("Las celdas de texto CSV no pueden iniciar con fórmulas.")
    return value


def _normalizar_calificacion(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Decimal], dict[str, Decimal]]:
    modo = payload.get("modo", "FACTORES").upper()
    montos = {nombre: Decimal(str(payload.get(nombre, 0) or 0)) for nombre in MONTOS}
    factores = {nombre: Decimal(str(payload.get(nombre, 0) or 0)) for nombre in FACTORES}
    if modo == "MONTOS":
        factores = calcular_factores_desde_montos(montos)
    elif modo != "FACTORES":
        raise ValueError("El modo debe ser MONTOS o FACTORES.")
    validar_factores_8_a_19(factores)
    meta = {key: payload[key] for key in (
        "corredor_id", "ejercicio", "mercado", "instrumento", "fecha_pago",
        "secuencia", "numero_dividendo", "tipo_sociedad", "valor_historico",
        "acogido_isfut", "factor_actualizacion", "descripcion", "origen",
    ) if key in payload}
    meta.setdefault("origen", "CORREDORA")
    meta["fuente_ingreso"] = payload.get("fuente_ingreso") or "MANUAL"
    meta["estado"] = payload.get("estado", "Pendiente")
    return meta, montos, factores


def guardar_calificacion(payload: dict[str, Any], usuario: str, ip_cliente: str | None = None) -> dict[str, Any]:
    meta, montos, factores = _normalizar_calificacion(payload)
    columnas = list(meta) + list(MONTOS) + list(FACTORES)
    valores = [meta[key] for key in meta] + [montos[key] for key in MONTOS] + [factores[key] for key in FACTORES]
    insert_cols = ", ".join(columnas)
    placeholders = ", ".join(["%s"] * len(valores))
    updates = ", ".join(f"{key}=EXCLUDED.{key}" for key in columnas if key not in LLAVE_CALIFICACION and key != "origen")
    query = f"""INSERT INTO calificaciones_tributarias ({insert_cols})
        VALUES ({placeholders}) ON CONFLICT ({', '.join(LLAVE_CALIFICACION)})
        DO UPDATE SET {updates}, fecha_ultima_modificacion=CURRENT_TIMESTAMP
        WHERE calificaciones_tributarias.origen <> 'SISTEMA'
        RETURNING id, (xmax = 0) AS insertado"""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(query, valores)
            row = cursor.fetchone()
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()
    if not row:
        raise ValueError("No se puede modificar un registro SISTEMA.")
    registrar_log_auditoria(usuario, "UPSERT_CALIFICACION", f"Calificación {row[0]} guardada.", "EXITO", ip_cliente)
    return {"id": row[0], "accion": "insertado" if row[1] else "actualizado"}


def listar_calificaciones(corredor_id: int | None, filtros: dict[str, Any]) -> list[dict[str, Any]]:
    where = []
    params: list[Any] = []
    if corredor_id is not None:
        where.append("corredor_id = %s")
        params.append(corredor_id)
    for key in ("mercado", "origen", "ejercicio", "estado", "instrumento"):
        if filtros.get(key) not in (None, ""):
            where.append(f"{key} = %s")
            params.append(filtros[key])
    fields = ["id", *LLAVE_CALIFICACION[1:], "numero_dividendo", "tipo_sociedad", "valor_historico",
              "acogido_isfut", "factor_actualizacion", "descripcion", "origen", "fuente_ingreso",
              "estado", "fecha_creacion", "fecha_ultima_modificacion", *FACTORES]
    where_clause = f" WHERE {' AND '.join(where)}" if where else ""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                f"SELECT {', '.join(fields)} FROM calificaciones_tributarias"
                f"{where_clause} ORDER BY ejercicio DESC, id DESC",
                params,
            )
            rows = cursor.fetchall()
            return [dict(zip(fields, row)) for row in rows]
    finally:
        conexion.close()


def cambiar_estado_calificacion(
    id_calificacion: int,
    nuevo_estado: str,
    usuario: str,
    ip_cliente: str | None = None,
) -> dict[str, Any]:
    if nuevo_estado not in ("Aprobado", "Rechazado"):
        raise ValueError("El nuevo estado debe ser Aprobado o Rechazado.")
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT estado, origen, mercado, instrumento, secuencia
                FROM calificaciones_tributarias
                WHERE id = %s
                FOR UPDATE
                """,
                (id_calificacion,),
            )
            calificacion = cursor.fetchone()
            if not calificacion:
                raise LookupError("Calificación no encontrada.")
            if calificacion[1] == "SISTEMA":
                raise ValueError("Los registros SISTEMA no se pueden aprobar ni rechazar.")
            if calificacion[0] != "Pendiente":
                raise ValueError("Solo se pueden aprobar o rechazar calificaciones Pendientes.")
            cursor.execute(
                """
                UPDATE calificaciones_tributarias
                SET estado = %s, fecha_ultima_modificacion = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, estado
                """,
                (nuevo_estado, id_calificacion),
            )
            resultado = cursor.fetchone()
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()
    registrar_log_auditoria(
        usuario,
        "CAMBIO_ESTADO_CALIFICACION",
        f"Calificación {id_calificacion} ({calificacion[2]} / {calificacion[3]} / secuencia {calificacion[4]}): estado cambiado a {nuevo_estado}.",
        nuevo_estado.upper(),
        ip_cliente,
    )
    return {"id": resultado[0], "estado": resultado[1]}


def eliminar_calificacion(id_calificacion: int, corredor_id: int, usuario: str, ip_cliente: str | None = None) -> None:
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT origen FROM calificaciones_tributarias WHERE id=%s AND corredor_id=%s", (id_calificacion, corredor_id))
            row = cursor.fetchone()
            if not row:
                raise LookupError("Calificación no encontrada.")
            if row[0] == "SISTEMA":
                raise ValueError("Los registros SISTEMA no se pueden eliminar.")
            cursor.execute("DELETE FROM calificaciones_tributarias WHERE id=%s AND corredor_id=%s", (id_calificacion, corredor_id))
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()
    registrar_log_auditoria(usuario, "ELIMINAR_CALIFICACION", f"Calificación {id_calificacion} eliminada.", "EXITO", ip_cliente)


def listar_declaraciones(
    estado: str | None = None,
    periodo_tributario: int | None = None,
    rut_empresa: str | None = None,
) -> list[dict[str, Any]]:
    filtros = []
    parametros: list[Any] = []
    if estado:
        filtros.append("d.estado = %s")
        parametros.append(estado)
    if periodo_tributario is not None:
        filtros.append("d.periodo_tributario = %s")
        parametros.append(periodo_tributario)
    if rut_empresa:
        filtros.append("d.rut_empresa = %s")
        parametros.append(rut_empresa)

    where = f"WHERE {' AND '.join(filtros)}" if filtros else ""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT d.id, d.folio, d.rut_empresa, d.periodo_tributario,
                       d.estado, d.id_usuario_creador, d.fecha_creacion,
                       f.suma_factores_criticos, f.es_valido
                FROM declaraciones_tributarias d
                LEFT JOIN factores_tributarios f ON f.id_declaracion = d.id
                {where}
                ORDER BY d.fecha_creacion DESC, d.id DESC
                """,
                tuple(parametros),
            )
            filas = cursor.fetchall()
            return [
                {
                    "id": fila[0],
                    "folio": fila[1],
                    "rut_empresa": fila[2],
                    "periodo_tributario": fila[3],
                    "estado": fila[4],
                    "id_usuario_creador": fila[5],
                    "fecha_creacion": fila[6],
                    "suma_factores_criticos": (
                        str(fila[7]) if fila[7] is not None else None
                    ),
                    "es_valido": fila[8],
                }
                for fila in filas
            ]
    finally:
        conexion.close()


def obtener_detalle_declaracion(id_declaracion: int) -> dict[str, Any] | None:
    columnas_factores = ", ".join(
        f"f.factor_{indice}" for indice in range(1, 30)
    )
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT d.id, d.folio, d.rut_empresa, d.periodo_tributario,
                       d.estado, d.id_usuario_creador, d.fecha_creacion,
                       f.suma_factores_criticos, f.es_valido, {columnas_factores}
                FROM declaraciones_tributarias d
                LEFT JOIN factores_tributarios f ON f.id_declaracion = d.id
                WHERE d.id = %s
                """,
                (id_declaracion,),
            )
            fila = cursor.fetchone()
            if not fila:
                return None
            return {
                "id": fila[0],
                "folio": fila[1],
                "rut_empresa": fila[2],
                "periodo_tributario": fila[3],
                "estado": fila[4],
                "id_usuario_creador": fila[5],
                "fecha_creacion": fila[6],
                "suma_factores_criticos": (
                    str(fila[7]) if fila[7] is not None else None
                ),
                "es_valido": fila[8],
                "factores": [
                    str(valor) if valor is not None else "0.00000000"
                    for valor in fila[9:]
                ],
            }
    finally:
        conexion.close()


def cambiar_estado_declaracion(
    id_declaracion: int,
    nuevo_estado: str,
    id_usuario: int,
    comentario: str | None = None,
) -> dict[str, Any]:
    if nuevo_estado not in ("Aprobado", "Rechazado"):
        raise ValueError("El nuevo estado debe ser Aprobado o Rechazado.")

    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT estado
                FROM declaraciones_tributarias
                WHERE id = %s
                FOR UPDATE
                """,
                (id_declaracion,),
            )
            declaracion = cursor.fetchone()
            if not declaracion:
                raise LookupError("Declaración no encontrada.")
            if declaracion[0] != "Pendiente":
                raise ValueError(
                    "Solo se pueden aprobar o rechazar declaraciones Pendientes."
                )
            cursor.execute(
                """
                UPDATE declaraciones_tributarias
                SET estado = %s
                WHERE id = %s
                RETURNING id, estado
                """,
                (nuevo_estado, id_declaracion),
            )
            resultado = cursor.fetchone()
        conexion.commit()
        return {
            "id": resultado[0],
            "estado": resultado[1],
            "id_usuario": id_usuario,
            "comentario": comentario,
        }
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()
