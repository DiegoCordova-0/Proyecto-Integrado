import os
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def obtener_coleccion_logs():
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("Error: MONGO_URI no configurada en el archivo .env")
        return None
    try:
        client = MongoClient(mongo_uri)
        db = client["nuam_audit"]
        return db["audit_logs"]
    except Exception as e:
        print(f"Error al conectar a MongoDB: {e}")
        return None

def registrar_log_auditoria(rut_usuario, accion, detalle, estado="EXITO"):
    coleccion = obtener_coleccion_logs()
    if coleccion is not None:
        log = {
            "rut_usuario": rut_usuario,
            "accion": accion,
            "detalle": detalle,
            "estado": estado,
            "fecha_hora": datetime.utcnow().isoformat()
        }
        resultado = coleccion.insert_one(log)
        print(f"Log de auditoría registrado en MongoDB (ID: {resultado.inserted_id})")
        return True
    return False

if __name__ == "__main__":
    # Prueba de inserción
    registrar_log_auditoria("12345678-9", "TEST_CONEXION", "Prueba de integración MongoDB")