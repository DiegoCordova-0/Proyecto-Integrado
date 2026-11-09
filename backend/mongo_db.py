import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()


def obtener_coleccion_logs():
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("Error: MONGO_URI no configurada en el archivo .env")
        return None
    try:
        cliente = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        cliente.admin.command("ping")
        return cliente["nuam_audit"]["audit_logs"]
    except Exception as error:
        print(f"Error al conectar a MongoDB: {error}")
        return None


def registrar_log_auditoria(
    rut_usuario, accion, detalle, estado="EXITO", ip_cliente=None
):
    coleccion = obtener_coleccion_logs()
    if coleccion is None:
        return False

    log = {
        "rut_usuario": rut_usuario,
        "accion": accion,
        "detalle": detalle,
        "estado": estado,
        "fecha_hora": datetime.now(timezone.utc).isoformat(),
        "ip_cliente": ip_cliente,
    }
    try:
        coleccion.insert_one(log)
        return True
    except Exception as error:
        print(f"Error al registrar auditoría en MongoDB: {error}")
        return False


def almacenar_csv_crudo(
    nombre_archivo: str,
    contenido: str,
    rut_usuario: str,
    cantidad_filas: int,
    ip_cliente: str | None = None,
):
    coleccion = obtener_coleccion_logs()
    if coleccion is None:
        return False
    documento = {
        "nombre_archivo": nombre_archivo,
        "contenido_crudo": contenido,
        "rut_usuario": rut_usuario,
        "cantidad_filas": cantidad_filas,
        "fecha_hora": datetime.now(timezone.utc).isoformat(),
        "ip_cliente": ip_cliente,
    }
    try:
        coleccion.database["raw_csv_files"].insert_one(documento)
        return True
    except Exception as error:
        print(f"Error al almacenar CSV crudo en MongoDB: {error}")
        return False


def listar_logs_auditoria(limit=100, skip=0):
    coleccion = obtener_coleccion_logs()
    if coleccion is None:
        raise RuntimeError("MongoDB no está disponible.")
    try:
        cursor = (
            coleccion.find({}, {"_id": 0})
            .sort("fecha_hora", -1)
            .skip(skip)
            .limit(limit)
        )
        return list(cursor)
    except Exception as error:
        print(f"Error al consultar auditoría en MongoDB: {error}")
        raise RuntimeError("No fue posible consultar la auditoría.") from error

print("--- Probando conexion a MongoDB ---")
resultado = registrar_log_auditoria("11111111-1", "TEST_CONEXION", "Prueba de terminal")
print("Resultado de la prueba:", resultado)