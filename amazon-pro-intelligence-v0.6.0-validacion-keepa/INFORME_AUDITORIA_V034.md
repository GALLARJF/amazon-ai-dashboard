# Auditoría de V0.3.4 (punto de partida de V0.4.0)
**Método**: lectura del código, ejecución de 15 suites (≈480 comprobaciones) y revisión del relato de la primera llamada real. Claude no ha hecho ninguna llamada real a OpenAI ni a Keepa.

## Real, simulado y pendiente
| Elemento | Estado |
|---|---|
| Servidor local 127.0.0.1, SQLite, auditoría encadenada, roles, CSRF, CSP | REAL (probado con tests y navegador) |
| Adaptador OpenAI Responses, presupuestos, consentimiento, guardia de 1ª llamada | REAL en código; llamadas **simuladas** en tests |
| Primera llamada real que comunicas (gpt-6-luna, 1.299 in / 550 out, 8.772 ms, 0,000405 USD) | NO verificable por Claude. Cálculo coherente: 1.299×0,10 + 550×0,50 por millón = 0,000405 USD. El id `resp_…` y la facturación solo puedes confirmarlos tú en el panel de OpenAI |
| Alcance de ese «GO» | Aplica **solo al expediente SINTÉTICO**. No es un GO para PHIVITAL ni ACTIVCORE |
| Conectores Amazon | NINGUNO (desactivados; sin credenciales) |
| Datos de mercado reales | NINGUNO hasta usar Keepa |

## Hallazgos
1. La contraseña de admin solo se mostraba al crear la base de datos → resuelto en V0.3.4 con `RESTABLECER_ADMIN.bat`.
2. Cuenta por defecto: al añadir ACTIVCORE se evitó que desplazara a PHIVITAL (regresión detectada por test y corregida).
3. Textos «V0.3» residuales en docstrings/estado: cosméticos, pendientes de limpieza.
4. No probado en Windows real (solo Linux + Chromium).
