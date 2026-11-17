# Resultados de tests (V0.4.0) — `bash tests/run_all.sh`
Todo en verde, sin red (Keepa y OpenAI simulados). Detalle completo: `tests/resultado_ejecucion_final.txt`.
| Suite | Resultado |
|---|---|
| Heredadas V0.2/V0.3 (calc, economía, expediente, integración, paridad, store, backend, ámbito, OpenAI, presupuesto, documentación, claves, API, seguridad, esquema, UI) | OK |
| V0.3.4 (confirmación, UI sintética 15/15, restablecer admin 21/21) | OK |
| **V0.4.0 Keepa** | 27/27 |
| **V0.4.0 motor europeo** | 30/30 |
| **V0.4.0 API + Director EU** | 45/45 |
| **V0.4.0 UI Europa (Playwright)** | 21/21 |
Cubre: ACL por cuenta/rol, CSRF, clave centinela ausente de BD/HTML/exports, 429/401/incompletos, caché y presupuesto, NO EVALUABLE sin datos, ESCENARIO HIPOTÉTICO, consentimiento y cancelación del Director, bloqueo de 1ª llamada real, texto de inyección tratado como dato, móvil 390 px sin desbordamiento. Capturas reales: `CAPTURAS_UI/`.
**Límite**: no probado en Windows real ni contra Keepa/OpenAI reales.
