# Primera llamada real a OpenAI (V0.3.3) — instrucciones sencillas

> **Windows sin programar:** usa `LEEME_WINDOWS_CLAVE.md` (scripts `CONFIGURAR_CLAVE.bat`, `VERIFICAR_CONFIGURACION.bat`, `INICIAR.bat`). El archivo de la clave es `C:\Users\<usuario>\AmazonPro\ai.env`; en Linux/Mac, `~/AmazonPro/ai.env` (o la ruta de `AMAZON_PRO_ENV_FILE`). Los pasos 2–4 de abajo equivalen a eso.

**Estado actual: ninguna llamada hecha, ninguna clave en el sistema. Nadie te pedirá pegar la clave en el chat: va solo en un archivo de tu equipo.**

1. Crea un *proyecto* de OpenAI «amazon-pro» con **límite de gasto mensual** en el panel (segunda barrera independiente de la de la app) y una clave solo para él.
2. Copia `config/openai.env.example` a un archivo **fuera de la carpeta del proyecto** (p. ej. `~/.amazon_pro_ai.env`), pon la clave en `OPENAI_API_KEY` y deja `AMAZON_PRO_AI_ENABLE=0`.
3. *(Opcional, sin generar tokens)* `set -a; source ~/.amazon_pro_ai.env; set +a; python3 tools/check_openai_models.py --yes` → comprueba que tu cuenta ve `gpt-6-luna`.
4. **Preflight (sin red, sin gasto):** `python3 tools/preflight_primera_llamada.py` con las variables cargadas. Revisa estado, presupuestos, peor caso (≈ 0,0014 USD) y el texto exacto que saldría. Debe acabar en «LISTO PARA LLAMAR» una vez `ENABLE=1`.
5. Cuando **tú** autorices el gasto: `AMAZON_PRO_AI_ENABLE=1`, arranca `python3 server.py`, entra como admin (la contraseña del primer arranque sale en consola).
6. Director → cuenta **«Sintético · primera llamada real»** → expediente **SINTÉTICO · Magnesio PRUEBA** → «resumen general». Es el único expediente que puede salir hacia OpenAI hasta verificar.
7. Comprueba en Historial: modo **REAL**, modelo, tokens *reportados por el proveedor*, coste, anclaje OK. Solo entonces la app declara «IA real verificada» y se levanta la guardia.
8. Compara el coste con el panel de OpenAI. Si alguna ejecución quedó **INCIERTA** (timeout, 5xx), concílala con el coste del panel: `POST /api/ai/reconcile {"id": "...", "actual_cost": X}` (admin).

**Parar:** `AMAZON_PRO_AI_ENABLE=0` y reiniciar. **Si algo sale mal:** no se reintenta nada automáticamente; revisa el registro de la ejecución (código de error) y el panel de OpenAI.
