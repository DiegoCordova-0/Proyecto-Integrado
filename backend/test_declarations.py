import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from backend.declarations import (
    cambiar_estado_calificacion,
    cambiar_estado_declaracion,
    guardar_calificacion,
    listar_declaraciones,
    obtener_detalle_declaracion,
    validate_csv_text_cell,
    _normalizar_calificacion,
)
from backend.main import CalificacionRequest, consultar_calificaciones


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
    def test_rechaza_texto_csv_que_parece_formula(self):
        for value in ("=1+1", " +cmd", "-formula", "@SUM(A1:A2)"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "no pueden iniciar con fórmulas"):
                    validate_csv_text_cell(value)
        self.assertEqual(validate_csv_text_cell("Copec"), "Copec")

    @patch("backend.declarations.obtener_conexion")
    def test_aprobador_lista_todos_los_estados_sin_where_vacio(self, obtener_conexion):
        conexion = FakeConnection([])
        obtener_conexion.return_value = conexion

        resultado = consultar_calificaciones(
            estado="",
            usuario=SimpleNamespace(rol="Aprobador", id=7),
        )

        query, params = conexion.cursor_instance.executions[0]
        self.assertEqual(resultado, [])
        self.assertNotIn("WHERE", query)
        self.assertIn("FROM calificaciones_tributarias ORDER BY", query)
        self.assertEqual(params, [])

    @patch("backend.main.listar_calificaciones", return_value=[])
    def test_consultar_calificaciones_sin_filtro_todos_los_estados(self, listar):
        usuario = SimpleNamespace(rol="Aprobador", id=7)

        for estado in ("", "TODOS", " todos "):
            with self.subTest(estado=estado):
                consultar_calificaciones(estado=estado, usuario=usuario)
                self.assertIsNone(listar.call_args.args[1]["estado"])

    @patch("backend.declarations.registrar_log_auditoria")
    @patch("backend.declarations.obtener_conexion")
    def test_fuente_ingreso_manual_nunca_se_guarda_como_null(
        self, obtener_conexion, _registrar_log
    ):
        base_request = {
            "ejercicio": 2026,
            "mercado": "ACN",
            "instrumento": "Instrumento",
            "fecha_pago": datetime(2026, 1, 1),
            "secuencia": 10001,
            "valor_historico": "0",
            "factor_actualizacion": "0",
        }

        for incluir_fuente, fuente in ((False, None), (True, None)):
            with self.subTest(incluir_fuente=incluir_fuente):
                request_data = dict(base_request)
                if incluir_fuente:
                    request_data["fuente_ingreso"] = fuente
                payload = CalificacionRequest(**request_data).to_payload(7)
                self.assertEqual(payload["fuente_ingreso"], "MANUAL")

                conexion = FakeConnection([(7, True)])
                obtener_conexion.return_value = conexion
                guardar_calificacion(payload, "11111111-1")

                query, params = conexion.cursor_instance.executions[0]
                columnas = query.split("(", 1)[1].split(")", 1)[0].split(", ")
                self.assertEqual(params[columnas.index("fuente_ingreso")], "MANUAL")

    def test_normalizacion_preserva_fuente_de_carga_csv(self):
        for fuente in ("CSV_MONTOS", "CSV_FACTORES"):
            with self.subTest(fuente=fuente):
                meta, _, _ = _normalizar_calificacion(
                    {"modo": "FACTORES", "fuente_ingreso": fuente}
                )
                self.assertEqual(meta["fuente_ingreso"], fuente)

    @patch("backend.declarations.registrar_log_auditoria")
    @patch("backend.declarations.obtener_conexion")
    def test_cambia_estado_de_calificacion_y_audita(self, obtener_conexion, registrar_log):
        conexion = FakeConnection([
            ("Pendiente", "CORREDORA", "ACN", "Copec", 10001),
            (7, "Aprobado"),
        ])
        obtener_conexion.return_value = conexion

        resultado = cambiar_estado_calificacion(7, "Aprobado", "11111111-1")

        self.assertEqual(resultado, {"id": 7, "estado": "Aprobado"})
        self.assertTrue(conexion.committed)
        registrar_log.assert_called_once()

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
