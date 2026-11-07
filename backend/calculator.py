from decimal import Decimal, InvalidOperation, ROUND_DOWN
from typing import Sequence

from .database import obtener_conexion
from .mongo_db import registrar_log_auditoria

ESCALA_8_DECIMALES = Decimal("0.00000001")
LIMITE_FACTORES = Decimal("1.00000000")
TOTAL_FACTORES = 29


def truncar_8_decimales(valor: Decimal | str | int) -> Decimal:
    """Trunca un valor decimal sin convertirlo a punto flotante binario."""
    try:
        decimal = Decimal(str(valor))
    except (InvalidOperation, ValueError) as error:
        raise ValueError(f"Factor inválido: {valor}") from error

    if not decimal.is_finite() or decimal < 0:
        raise ValueError("Los factores deben ser decimales finitos no negativos.")
    return decimal.quantize(ESCALA_8_DECIMALES, rounding=ROUND_DOWN)


def procesar_factores_tributarios(
    rut_usuario: str,
    id_declaracion: int,
    lista_factores: Sequence[Decimal | str | int],
    ip_cliente: str | None = None,
) -> dict:
    """Valida y persiste exactamente 29 factores con precisión decimal exacta."""
    if len(lista_factores) != TOTAL_FACTORES:
        return {
            "exito": False,
            "mensaje": (
                f"Se esperaban {TOTAL_FACTORES} factores, "
                f"se recibieron {len(lista_factores)}."
            ),
        }

    try:
        factores_procesados = [truncar_8_decimales(factor) for factor in lista_factores]
    except ValueError as error:
        return {"exito": False, "mensaje": str(error)}

    suma_total = sum(factores_procesados, Decimal("0.00000000"))
    if suma_total > LIMITE_FACTORES:
        registrar_log_auditoria(
            rut_usuario,
            "VALIDACION_FACTORES_RECHAZADA",
            f"Declaración {id_declaracion}: suma {suma_total} supera {LIMITE_FACTORES}.",
            "RECHAZADO",
            ip_cliente,
        )
        return {
            "exito": False,
            "mensaje": f"La suma total es {suma_total}, excede el límite permitido de {LIMITE_FACTORES}.",
            "suma_calculada": str(suma_total),
        }

    conexion = None
    try:
        conexion = obtener_conexion()
        columnas = ", ".join(
            f"factor_{indice}" for indice in range(1, TOTAL_FACTORES + 1)
        )
        valores = ", ".join(["%s"] * TOTAL_FACTORES)
        actualizaciones = ", ".join(
            f"factor_{indice} = EXCLUDED.factor_{indice}"
            for indice in range(1, TOTAL_FACTORES + 1)
        )
        query = f"""
            INSERT INTO factores_tributarios
                (id_declaracion, {columnas}, suma_factores_criticos, es_valido)
            VALUES (%s, {valores}, %s, %s)
            ON CONFLICT (id_declaracion) DO UPDATE SET
                {actualizaciones},
                suma_factores_criticos = EXCLUDED.suma_factores_criticos,
                es_valido = EXCLUDED.es_valido,
                fecha_calculo = CURRENT_TIMESTAMP
        """
        with conexion.cursor() as cursor:
            cursor.execute(
                query,
                (id_declaracion, *factores_procesados, suma_total, True),
            )
        conexion.commit()
    except Exception as error:
        if conexion is not None:
            conexion.rollback()
        return {"exito": False, "mensaje": f"Error al guardar en Supabase: {error}"}
    finally:
        if conexion is not None:
            conexion.close()

    registrar_log_auditoria(
        rut_usuario,
        "CALCULO_FACTORES_EXITO",
        f"Declaración {id_declaracion} persistida. Suma: {suma_total}.",
        "EXITO",
        ip_cliente,
    )
    return {
        "exito": True,
        "mensaje": "Factores procesados y persistidos exitosamente.",
        "suma_calculada": str(suma_total),
        "factores": [str(factor) for factor in factores_procesados],
    }
