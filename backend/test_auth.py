import os
import unittest
from datetime import timedelta
from unittest.mock import patch

import bcrypt
import jwt
from fastapi import HTTPException

from backend.auth import (
    ALGORITHM,
    UsuarioActual,
    _crear_token,
    autenticar_usuario,
    obtener_usuario_actual,
    requerir_roles,
)


class AuthTests(unittest.TestCase):
    def setUp(self):
        os.environ["JWT_SECRET_KEY"] = "test-secret-key-with-at-least-32-chars"

    def test_crea_token_con_tipo_y_expiracion(self):
        token = _crear_token("7", "Analista", "access", timedelta(minutes=15))
        payload = jwt.decode(
            token,
            os.environ["JWT_SECRET_KEY"],
            algorithms=[ALGORITHM],
        )
        self.assertEqual(payload["sub"], "7")
        self.assertEqual(payload["type"], "access")
        self.assertEqual(payload["rol"], "Analista")

    @patch("backend.auth._crear_refresh_token", return_value="refresh-token")
    @patch("backend.auth._buscar_usuario")
    def test_login_verifica_bcrypt(self, buscar_usuario, _crear_refresh):
        hash_password = bcrypt.hashpw(
            b"password-segura", bcrypt.gensalt()
        ).decode("utf-8")
        buscar_usuario.return_value = (
            7,
            "11111111-1",
            "analista@example.com",
            "Ana",
            hash_password,
            "Analista",
        )

        respuesta = autenticar_usuario("analista@example.com", "password-segura")

        self.assertEqual(respuesta.refresh_token, "refresh-token")
        self.assertTrue(respuesta.access_token)

    @patch("backend.auth._buscar_usuario", return_value=None)
    def test_login_rechaza_credenciales_invalidas(self, _buscar_usuario):
        with self.assertRaises(HTTPException) as contexto:
            autenticar_usuario("no-existe", "password-segura")
        self.assertEqual(contexto.exception.status_code, 401)

    def test_requerir_roles_rechaza_rol_no_autorizado(self):
        dependencia = requerir_roles("Analista")
        usuario = UsuarioActual(
            id=1,
            rut="1-9",
            email="auditor@example.com",
            nombre="Auditor",
            rol="Auditor",
        )
        with self.assertRaises(HTTPException) as contexto:
            dependencia(usuario)
        self.assertEqual(contexto.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
