#!/usr/bin/env bash
# Ejecuta TODAS las pruebas V0.5.0 y FALLA si alguna falla. Uso: bash tests/run_all.sh (requiere node, python3, playwright, jsonschema)
cd "$(dirname "$0")/.."; FAIL=0
run(){ echo "== $1"; shift; o=$("$@" 2>&1); rc=$?; echo "$o" | tail -1; [ $rc -ne 0 ] && { echo "   >>> FALLO (rc=$rc)"; FAIL=1; }; }
for f in calc economics dossier integration; do run "js/$f (heredado V0.2)" node tests/$f.test.js; done
run "paridad JS↔Python" python3 tests/parity_test.py
run "store/auditoría" python3 tests/store_test.py
run "backend (motor, coworkers, piloto, IA, Director)" python3 tests/backend_test.py
run "ámbito/compatibilidad de contrato (JS)" node tests/scope_test.js
run "OpenAI (Responses, presupuestos, E2E, sin consumo real)" python3 tests/openai_test.py
run "presupuesto: concurrencia, reintentos, timeouts, consumo incierto" python3 tests/budget_test.py
run "IDs/tarifas == documentación oficial" python3 tests/docs_match_test.py
run "V0.3.3: ACL usage, no-fuga de clave, sintético, guardia 1ª llamada" python3 tests/v032_test.py
run "V0.3.3: archivo local de clave, Windows, ENABLE=0 => cero llamadas" python3 tests/envfile_test.py
run "API (auth, roles, aislamiento, Director, aprobaciones)" python3 tests/api_test.py
run "seguridad (heredada V0.2)" python3 tests/security_test.py
run "esquema" python3 tests/schema_test.py
run "UI (navegador real + capturas)" python3 tests/ui_test.py
run "V0.3.4: confirmación, procedencia OpenAI, registro mínimo, explicaciones" python3 tests/v034_test.py
run "V0.3.4: UI prueba sintética (desplegable, confirmación, errores)" python3 tests/ui_synth_test.py
run "V0.3.4: restablecer contraseña de admin (conserva datos y ai.env)" python3 tests/reset_admin_test.py
run "V0.4.0: Keepa (cliente, tokens, caché, 429, incompleto, sin claves)" python3 tests/keepa_test.py
run "V0.4.0: motor europeo (economía, benchmark, ranking, sensibilidad)" python3 tests/eu_test.py
run "V0.4.0: API europea + Director EU (ACL, CSRF, consentimiento, anclaje)" python3 tests/v040_api_test.py
run "V0.4.0: UI EUROPA · ACTIVCORE (navegador real + capturas)" python3 tests/ui_eu_test.py
run "V0.5.0: catálogo, descubrimiento, aislamiento, costes, ACL" python3 tests/v050_test.py
run "V0.5.0: UI Categoría→Producto→ANALIZAR EUROPA (navegador real + capturas)" python3 tests/ui_eu_test.py
run "V0.5.0: lanzador Windows (lógica)" python3 tests/launcher_test.py
run "V0.6.0: operación (tareas, N1–N4, bandeja, modelos, libro, economía, expediente, importador, API)" python3 tests/v060_test.py
run "V0.6.0: UI cinco espacios NEON (navegador real + capturas)" python3 tests/ui_v06_test.py
run "V0.6.0 misión Keepa: presupuesto, duplicados, errores, persistencia (MOCK)" python3 tests/keepa_mision_test.py
run "V0.6.0 misión Keepa: flujo Director IA con tope 10 (MOCK)" python3 tests/keepa_mision_flow_test.py
run "V0.6.0 misión Keepa: coherencia de evidencias REALES (lectura de ficheros)" python3 tests/keepa_real_evidence_test.py
run "V0.7.0: datos reales de Keepa integrados (sin red ni gasto)" python3 tests/v070_keepa_real_test.py
run "V0.7.0: expediente comercial ACTIVCORE" python3 tests/v070_expediente_test.py
run "V0.7.0: Director IA, briefing determinista" python3 tests/v070_director_test.py
run "V0.7.0: seguridad de /api/v07/*" python3 tests/v070_security_test.py
run "V0.7.0: UI NEON (navegador real + capturas)" python3 tests/ui_v07_test.py
run "V0.7.0: ciclo de desarrollo autónomo (3 intentos, bloqueo, dependencias)" python3 tests/desarrollo_test.py
run "V1.0: relevo (bloqueo de concurrencia, recuperación, commit controlado)" python3 tests/relevo_test.py
run "V1.0: matriz de aceptación (4 categorías)" python3 tests/v100_matriz_test.py
run "V1.0: PREPARAR Y LANZAR extremo a extremo con persistencia" python3 tests/v100_lanzar_test.py
run "V1.0: VENDER Y OPTIMIZAR con CSV importados (simulados, etiquetados)" python3 tests/v100_vender_test.py
run "V1.0: motor financiero (escenarios, sensibilidad, equilibrio)" python3 tests/v100_finanzas_test.py
run "V1.0: exportaciones CSV/HTML/MD con trazabilidad" python3 tests/v100_export_test.py
run "V1.0: persistencia (respaldo, restauración, BD corrupta)" python3 tests/v100_persistencia_test.py
run "V1.0: ficha única de integraciones bloqueadas" python3 tests/v100_ficha_test.py
run "V1.0: interfaz NEON móvil/tableta/escritorio (Chromium real)" python3 tests/ui_v100_test.py
run "V1.0: Director IA plan de especialistas" python3 tests/v100_director_plan_test.py
run "V1.0: adaptadores SP-API/Ads solo lectura (simulados)" python3 tests/v100_conectores_test.py
run "V1.0: documentación verificable" python3 tests/v100_docs_test.py
run "V1.0: entrega candidata (informe, ZIP sin claves)" python3 tests/v100_entrega_test.py
run "V1.0: modo cloud (proceso real, HTTPS simulado, secretos, respaldo)" python3 tests/v100_cloud_test.py
run "V1.0: Chromium contra el modo cloud con proxy HTTPS" python3 tests/ui_v100_cloud_test.py
run "V1.0: respaldo fuera del disco, restauración y rotación de contraseñas" python3 tests/v100_respaldo_cloud_test.py
run "K1: Keepa seguro (modos, aprobación, tope, duplicados, concurrencia, comparabilidad) — simulado" python3 tests/k1_keepa_test.py
run "K1: capa HTTP de Keepa y descubrimiento — simulado" python3 tests/k1_http_test.py
run "K2: Director Amazon IA por intención (competidores, precio, país, faltantes, riesgos) — simulado" python3 tests/k2_director_test.py
run "K3: segmentación competitiva (motor, validación vs referencia, API, revisión, Director, persistencia, cloud) — simulado" python3 tests/k3_segmentacion_test.py
run "K3: interfaz NEON de segmentos (navegador real, escritorio/tablet/móvil)" python3 tests/ui_k3_test.py
run "K4: contratos, costes, medios con derechos, datos, pricing de 5 dictámenes y Director" python3 tests/k4_unit_test.py
run "K4 Consejero F1–F2: proveedores, libro de evidencias, verificador, motor y pruebas anti-plantilla (SIMULADO)" python3 tests/k4c_test.py
run "K4: planificador robusto (ejecución única, reintentos, recuperación, tope de gasto, parada)" python3 tests/k4_planner_test.py
run "K4 it.2: selección, umbrales, conciliación, informe, explorador, planificador (API)" python3 tests/k4_iter2_test.py
run "K4: API (roles, CSRF, aislamiento demo/producción, derechos de imagen, export, persistencia)" python3 tests/k4_api_test.py
run "K4: centro de mando NEON (navegador real, escritorio/tablet/móvil)" python3 tests/ui_k4_test.py
run "V0.7.0: registro de suites v0.7 en batería y coordinador" python3 tests/v070_registro_test.py
run "V0.7.0: entrega candidata (versión, informe real, ZIP sin claves)" python3 tests/v070_entrega_test.py
[ $FAIL -eq 0 ] && echo "TODAS LAS SUITES OK" || { echo "HAY SUITES CON FALLOS"; exit 1; }
