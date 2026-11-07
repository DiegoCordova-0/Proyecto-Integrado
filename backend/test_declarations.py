import unittest
from datetime import datetime
from unittest.mock import patch

from backend.declarations import (
    cambiar_estado_declaracion,
    listar_declaraciones,
    obtener_detalle_declaracion,
)


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.executions = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def execute(self, query, params):
        self.executions.append((query, params))

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None


class FakeConnection:
    def __init__(self, rows):
        self.cursor_instance = FakeCursor(rows)
        self.committed = False

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.committed = True

    def rollback(self):
        return None

    def close(self):
        return None


class DeclarationTests(unittest.TestCase):
    @patch("backend.declarations.obtener_conexion")
    def test_lista_con_filtros_parametrizados(self, obtener_conexion):
        conexion = FakeConnection(
            [
                (
                    4,
                    "F-4",
                    "76.123.456-7",
                    2026,
                    "Pendiente",
                    2,
                    datetime(2026, 1, 1),
                    "0.50000000",
                    True,
                )
            ]
        )
        obtener_conexion.return_value = conexion

        resultado = listar_declaraciones("Pendiente", 2026, "76.123.456-7")

        self.assertEqual(resultado[0]["id"], 4)
        self.assertEqual(
            conexion.cursor_instance.executions[0][1],
            ("Pendiente", 2026, "76.123.456-7"),
        )

    @patch("backend.declarations.obtener_conexion")
    def test_cambia_estado_solo_desde_pendiente(self, obtener_conexion):
        conexion = FakeConnection([( "Pendiente",), (4, "Aprobado")])
        obtener_conexion.return_value = conexion

        resultado = cambiar_estado_declaracion(4, "Aprobado", 9, "Revisado")

        self.assertEqual(resultado["estado"], "Aprobado")
        self.assertTrue(conexion.committed)

    @patch("backend.declarations.obtener_conexion")
    def test_rechaza_estado_de_origen_invalido(self, obtener_conexion):
        conexion = FakeConnection([("Borrador",)])
        obtener_conexion.return_value = conexion

        with self.assertRaises(ValueError):
            cambiar_estado_declaracion(4, "Aprobado", 9)

        self.assertFalse(conexion.committed)

    @patch("backend.declarations.obtener_conexion")
    def test_detalle_contiene_los_29_factores(self, obtener_conexion):
        conexion = FakeConnection(
            [
                (
                    4,
                    "F-4",
                    "76.123.456-7",
                    2026,
                    "Pendiente",
                    2,
                    datetime(2026, 1, 1),
                    "0.50000000",
                    True,
                    *([0] * 29),
                )
            ]
        )
        obtener_conexion.return_value = conexion

        resultado = obtener_detalle_declaracion(4)

        self.assertEqual(len(resultado["factores"]), 29)


if __name__ == "__main__":
    unittest.main()
