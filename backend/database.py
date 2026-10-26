import os
import psycopg2
from dotenv import load_dotenv

# Cargar las variables de entorno del archivo .env
load_dotenv()

def obtener_conexion():
    try:
        conexion = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT", "5432"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME", "postgres")
        )
        return conexion
    except Exception as e:
        print(f"Error al conectar a PostgreSQL/Supabase: {e}")
        return None

if __name__ == "__main__":
    conn = obtener_conexion()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM roles;")
        roles = cursor.fetchall()
        print("¡Conexión exitosa a Supabase!")
        print("Roles registrados en la base de datos:", roles)
        conn.close()