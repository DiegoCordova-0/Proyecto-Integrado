import bcrypt
from database import obtener_conexion

def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def crear_datos_prueba():
    conn = obtener_conexion()
    if not conn:
        print("Error: No se pudo conectar a PostgreSQL/Supabase.")
        return

    try:
        cursor = conn.cursor()

        # 1. Crear usuario Analista (id_rol = 1)
        pass_hash = hash_password("Analista123!")
        cursor.execute("""
            INSERT INTO usuarios (rut, nombre, email, password_hash, id_rol)
            VALUES (%s, %s, %s, %s, 1)
            ON CONFLICT (rut) DO UPDATE SET password_hash = EXCLUDED.password_hash;
        """, ('12345678-9', 'Analista Nuam', 'analista@nuam.com', pass_hash))

        # 2. Crear una Declaración Jurada de prueba (ID 1)
        cursor.execute("""
            INSERT INTO declaraciones_tributarias (id, folio, rut_empresa, periodo_tributario, id_usuario_creador, estado)
            VALUES (1, 'DJ-1949-2026-001', '76543210-K', 2026, (SELECT id FROM usuarios WHERE rut='12345678-9'), 'Borrador')
            ON CONFLICT (id) DO NOTHING;
        """)

        conn.commit()
        conn.close()
        print("--------------------------------------------------")
        print("¡Usuario Analista y Declaración ID 1 creados exitosamente!")
        print("RUT / Email: analista@nuam.com (o 12345678-9)")
        print("Contraseña:  Analista123!")
        print("--------------------------------------------------")

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        print(f"Error al poblar la base de datos: {e}")

if __name__ == "__main__":
    crear_datos_prueba()