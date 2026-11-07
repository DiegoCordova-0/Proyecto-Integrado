from typing import Any

from .database import obtener_conexion


ESTADOS_DECLARACION = ("Borrador", "Pendiente", "Aprobado", "Rechazado")


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
