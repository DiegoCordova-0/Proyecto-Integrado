# Reporte QA

- Fecha UTC: 2026-11-07T00:01:47.953280+00:00
- Resultado global: **PASS**
- Pruebas ejecutadas: **12**

## Resultados esperados vs. obtenidos

| Caso | Esperado | Obtenido | Discrepancia / causa raíz |
|---|---|---|---|
| `backend/test_auth.py::AuthTests::test_crea_token_con_tipo_y_expiracion` | PASS | PASS | Sin discrepancias. |
| `backend/test_auth.py::AuthTests::test_login_rechaza_credenciales_invalidas` | PASS | PASS | Sin discrepancias. |
| `backend/test_auth.py::AuthTests::test_login_verifica_bcrypt` | PASS | PASS | Sin discrepancias. |
| `backend/test_auth.py::AuthTests::test_requerir_roles_rechaza_rol_no_autorizado` | PASS | PASS | Sin discrepancias. |
| `backend/test_calculator.py::CalculatorTests::test_persiste_los_29_factores_como_decimales` | PASS | PASS | Sin discrepancias. |
| `backend/test_calculator.py::CalculatorTests::test_rechaza_cantidad_incorrecta` | PASS | PASS | Sin discrepancias. |
| `backend/test_calculator.py::CalculatorTests::test_rechaza_suma_un_centavo_de_nanounidad` | PASS | PASS | Sin discrepancias. |
| `backend/test_calculator.py::CalculatorTests::test_trunca_sin_redondear` | PASS | PASS | Sin discrepancias. |
| `backend/test_declarations.py::DeclarationTests::test_cambia_estado_solo_desde_pendiente` | PASS | PASS | Sin discrepancias. |
| `backend/test_declarations.py::DeclarationTests::test_detalle_contiene_los_29_factores` | PASS | PASS | Sin discrepancias. |
| `backend/test_declarations.py::DeclarationTests::test_lista_con_filtros_parametrizados` | PASS | PASS | Sin discrepancias. |
| `backend/test_declarations.py::DeclarationTests::test_rechaza_estado_de_origen_invalido` | PASS | PASS | Sin discrepancias. |

## Recomendaciones

Mantener las pruebas unitarias y agregar pruebas de integración con PostgreSQL y MongoDB.
