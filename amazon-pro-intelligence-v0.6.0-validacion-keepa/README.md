# Amazon Pro Intelligence V0.3.3 (AHT Executive Neon) — Conexión OpenAI lista para tu clave (Windows) · NO activada

> **V0.3.3:** archivo local seguro para la clave (`%USERPROFILE%\AmazonPro\ai.env`, fuera del proyecto y de GitHub), scripts `.bat` de Windows y guía sin programar: `LEEME_WINDOWS_CLAVE.md`. Sin clave puesta y con `ENABLE=0` no se hace ninguna llamada.

> **V0.3.2:** reserva atómica de presupuesto, consumo incierto conciliable, IDs/tarifas == docs oficiales, ACL de `/api/ai/usage`, clave nunca en logs/HTTP/BD/archivos, expediente SINTÉTICO único + guardia de primera llamada + preflight. Informe: `docs/INFORME_V0.3.2.md` · Guía: `docs/ACTIVAR_API_OPENAI.md`.

> **V0.3.1:** proveedor `openai` (Responses API) con tarifas oficiales verificadas, presupuestos por ejecución/mensual y registro de consumo. **Sin clave y sin ninguna llamada real: IA REAL no declarada.** Guía: `docs/ACTIVAR_API_OPENAI.md` · Informe: `docs/INFORME_OPENAI_V0.3.1.md` · Plantilla: `config/openai.env.example`.

Ejecutar: `python3 server.py` (Windows: `run.bat`) → http://localhost:8765 · solo 127.0.0.1 · sin dependencias de Python.
**Primer arranque:** la consola muestra la contraseña del usuario `admin` (solo esa vez; o fíjala con `AMAZON_PRO_ADMIN_PASSWORD`). Crea cuentas/usuarios con el panel de administración local o con `backend/store.py`.
Base de datos: `data/amazon_pro.db` (SQLite). Cuenta inicial: «PhiVital · Amazon.es» con titular legal **POR CONFIRMAR**.

## Estado honesto (lee esto primero)
- **IA real: PENDIENTE.** No había clave de proveedor. El adaptador y las pruebas funcionan con proveedor simulado y con un servidor local de pruebas; ninguna ejecución se declara real.
- **Coworkers:** 7, deterministas (sin IA ni datos externos). «Operativo» solo se muestra tras una ejecución verificada sobre datos del usuario **completos**; con datos DEMO/PRUEBA/INCOMPLETOS nunca.
- Sin conexiones externas por defecto; sin escritura en Amazon; sin credenciales de Amazon.

## Configurar la IA (opcional, desde variables de entorno del servidor; nunca en el navegador)
| Variable | Significado |
|---|---|
| `AMAZON_PRO_AI_PROVIDER` | `none` (defecto) · `mock` (SIMULADO) · `anthropic` · `openai_compat` |
| `ANTHROPIC_API_KEY` / `AMAZON_PRO_AI_API_KEY` | clave (solo servidor) |
| `AMAZON_PRO_AI_ENABLE=1` | consentimiento explícito para llamadas de pago |
| `AMAZON_PRO_AI_MODEL` | modelo a usar (obligatorio con proveedor real) |
| `AMAZON_PRO_AI_PRICE_IN` / `_PRICE_OUT` / `_CURRENCY` | precios por millón de tokens (los fija el operador; sin ellos el coste es «no calculado») |
| `AMAZON_PRO_AI_MAX_IN` / `_MAX_OUT` / `_MAX_COST` | presupuesto por ejecución |
| `AMAZON_PRO_AI_BASE_URL`, `AMAZON_PRO_AI_HOSTS` | endpoint alternativo y lista blanca de hosts (solo https) |

## Pruebas
`bash tests/run_all.sh` (node, python3, playwright, jsonschema). Demostraciones: `python3 demos/run_demos.py`.
## Documentación
`docs/INFORME_OPENAI_V0.3.1.md` · `docs/ACTIVAR_API_OPENAI.md` · `docs/INFORME_V0.3.md` · `docs/COMPATIBILIDAD_V0.2_V0.3.md` · `docs/BLOQUEOS_Y_PENDIENTES_V0.3.md` · `docs/PILOTO_PHIVITAL_MAGNESIO.md` · `demos/*.md` · heredadas de V0.2 en `docs/`.

## V0.3.4 — Prueba sintética segura visible en la interfaz
Expediente «SINTÉTICO · PRUEBA API» seleccionable en el Director; confirmación servidor-side antes de la primera llamada facturable; verificación de procedencia OpenAI (HTTPS api.openai.com, object=response, id, tokens reportados); registro mínimo `ai.call`; explicaciones de error en español. PHIVITAL y AHT Executive Neon sin cambios. Ver `LEEME_PRUEBA_API_V0.3.4.md`.

### Restablecer contraseña de admin
`RESTABLECER_ADMIN.bat` (+ `tools/restablecer_admin.py`): copia previa, solo cambia la contraseña de admin, cierra sesiones, no toca datos ni ai.env. Ver `LEEME_RESTABLECER_ADMIN.md`.
