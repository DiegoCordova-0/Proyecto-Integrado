import unittest
from decimal import Decimal
from unittest.mock import patch

from backend import calculator


class FakeCursor:
    def __init__(self):
        self.params = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def execute(self, _query, params):
        self.params = params


class FakeConnection:
    def __init__(self):
        self.cursor_instance = FakeCursor()
        self.committed = False

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.committed = True

    def rollback(self):
        raise AssertionError("No debe revertirse una transacción válida.")

    def close(self):
        return None


class CalculatorTests(unittest.TestCase):
    def test_trunca_sin_redondear(self):
        resultado = calculator.truncar_8_decimales("0.123456789")
        self.assertEqual(resultado, Decimal("0.12345678"))

    @patch("backend.calculator.registrar_log_auditoria")
    def test_rechaza_suma_un_centavo_de_nanounidad(self, registrar_log):
        factores = ["0.03448276"] * calculator.TOTAL_FACTORES
        resultado = calculator.procesar_factores_tributarios(
            "11111111-1", 10, factores
        )

        self.assertFalse(resultado["exito"])
        self.assertEqual(resultado["suma_calculada"], "1.00000004")
        registrar_log.assert_called_once()

    @patch("backend.calculator.registrar_log_auditoria")
    def test_persiste_los_29_factores_como_decimales(self, registrar_log):
        conexion = FakeConnection()
        factores = ["0.034482758"] + ["0"] * 28

        with patch("backend.calculator.obtener_conexion", return_value=conexion):
            resultado = calculator.procesar_factores_tributarios(
                "11111111-1", 11, factores
            )

        self.assertTrue(resultado["exito"])
        self.assertEqual(resultado["suma_calculada"], "0.03448275")
        self.assertEqual(len(resultado["factores"]), calculator.TOTAL_FACTORES)
        self.assertEqual(
            conexion.cursor_instance.params[1], Decimal("0.03448275")
        )
        self.assertTrue(conexion.committed)
        registrar_log.assert_called_once()

    def test_rechaza_cantidad_incorrecta(self):
        resultado = calculator.procesar_factores_tributarios(
            "11111111-1", 12, ["0"] * 28
        )
        self.assertFalse(resultado["exito"])
        self.assertIn("29 factores", resultado["mensaje"])


if __name__ == "__main__":
    unittest.main()
