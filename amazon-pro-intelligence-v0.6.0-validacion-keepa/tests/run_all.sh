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
run "V0.7.0: registro de suites v0.7 en batería y coordinador" python3 tests/v070_registro_test.py
run "V0.7.0: entrega candidata (versión, informe real, ZIP sin claves)" python3 tests/v070_entrega_test.py
[ $FAIL -eq 0 ] && echo "TODAS LAS SUITES OK" || { echo "HAY SUITES CON FALLOS"; exit 1; }
