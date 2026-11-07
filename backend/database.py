import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def obtener_conexion():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", "5432"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "postgres"),
        connect_timeout=int(os.getenv("DB_CONNECT_TIMEOUT", "5")),
    )
