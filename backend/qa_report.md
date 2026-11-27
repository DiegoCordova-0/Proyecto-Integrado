# Reporte QA

- Fecha UTC: 2026-11-27T20:45:43.220890+00:00
- Resultado global: **PASS**
- Pruebas ejecutadas: **20**

## Resultados esperados vs. obtenidos

| Caso | Esperado | Obtenido | Discrepancia / causa raíz |
|---|---|---|---|
| `backend/test_auth.py::AuthTests::test_crea_token_con_tipo_y_expiracion` | PASS | PASS | Sin discrepancias. |
| `backend/test_auth.py::AuthTests::test_login_rechaza_credenciales_invalidas` | PASS | PASS | Sin discrepancias. |
| `backend/test_auth.py::AuthTests::test_login_verifica_bcrypt` | PASS | PASS | Sin discrepancias. |
| `backend/test_auth.py::AuthTests::test_requerir_roles_rechaza_rol_no_autorizado` | PASS | PASS | Sin discrepancias. |
| `backend/test_calculator.py::CalculatorTests::test_convierte_montos_reales_a_factores` | PASS | PASS | Sin discrepancias. |
| `backend/test_calculator.py::CalculatorTests::test_persiste_los_29_factores_como_decimales` | PASS | PASS | Sin discrepancias. |
| `backend/test_calculator.py::CalculatorTests::test_rechaza_cantidad_incorrecta` | PASS | PASS | Sin discrepancias. |
| `backend/test_calculator.py::CalculatorTests::test_rechaza_suma_un_centavo_de_nanounidad` | PASS | PASS | Sin discrepancias. |
| `backend/test_calculator.py::CalculatorTests::test_trunca_sin_redondear` | PASS | PASS | Sin discrepancias. |
| `backend/test_calculator.py::CalculatorTests::test_valida_solo_factores_base_y_creditos_independientes` | PASS | PASS | Sin discrepancias. |
| `backend/test_declarations.py::DeclarationTests::test_aprobador_lista_todos_los_estados_sin_where_vacio` | PASS | PASS | Sin discrepancias. |
| `backend/test_declarations.py::DeclarationTests::test_cambia_estado_de_calificacion_y_audita` | PASS | PASS | Sin discrepancias. |
| `backend/test_declarations.py::DeclarationTests::test_cambia_estado_solo_desde_pendiente` | PASS | PASS | Sin discrepancias. |
| `backend/test_declarations.py::DeclarationTests::test_consultar_calificaciones_sin_filtro_todos_los_estados` | PASS | PASS | Sin discrepancias. |
| `backend/test_declarations.py::DeclarationTests::test_detalle_contiene_los_29_factores` | PASS | PASS | Sin discrepancias. |
| `backend/test_declarations.py::DeclarationTests::test_fuente_ingreso_manual_nunca_se_guarda_como_null` | PASS | PASS | Sin discrepancias. |
| `backend/test_declarations.py::DeclarationTests::test_lista_con_filtros_parametrizados` | PASS | PASS | Sin discrepancias. |
| `backend/test_declarations.py::DeclarationTests::test_normalizacion_preserva_fuente_de_carga_csv` | PASS | PASS | Sin discrepancias. |
| `backend/test_declarations.py::DeclarationTests::test_rechaza_estado_de_origen_invalido` | PASS | PASS | Sin discrepancias. |
| `backend/test_declarations.py::DeclarationTests::test_rechaza_texto_csv_que_parece_formula` | PASS | PASS | Sin discrepancias. |

## Recomendaciones

Mantener las pruebas unitarias y agregar pruebas de integración con PostgreSQL y MongoDB.
