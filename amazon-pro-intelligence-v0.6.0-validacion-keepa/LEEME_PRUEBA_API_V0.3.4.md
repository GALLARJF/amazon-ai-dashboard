# Prueba segura de la API (V0.3.4) — pasos para Windows

Tu clave ya está en `C:\Users\TU_USUARIO\AmazonPro\ai.env` (no se toca, no sale de ahí).

## Qué hay de nuevo
- Existe un expediente DEMO llamado **«SINTÉTICO · PRUEBA API»** (datos ficticios). Es el ÚNICO que puede enviarse a OpenAI en la primera llamada.
- Aparece en el desplegable del **Director Amazon IA** como «🧪 SINTÉTICO · PRUEBA API · PRUEBA», y hay un botón **«🧪 Probar API con expediente SINTÉTICO»**.
- PHIVITAL y los expedientes reales **no se modifican y no se envían**.
- Antes de la primera llamada facturable la app te pide **confirmación** (modelo, coste máximo, tope mensual y qué datos se envían).

## Pasos
1. Doble clic en `INICIAR.bat` y entra como `admin`.
2. Ve al Director Amazon IA. Verás «SIN IA» mientras la IA esté deshabilitada (es lo normal y no cuesta nada).
3. **Solo cuando TÚ autorices el gasto:** abre `ai.env` (con `CONFIGURAR_CLAVE.bat`), cambia `AMAZON_PRO_AI_ENABLE=0` por `AMAZON_PRO_AI_ENABLE=1`, comprueba que `AMAZON_PRO_AI_MONTHLY_BUDGET` tiene un tope (p. ej. 2), guarda y reinicia `INICIAR.bat`.
4. Pulsa **«🧪 Probar API con expediente SINTÉTICO»** (o elígelo en el desplegable y pregunta «resumen general»).
5. Sale el cuadro de confirmación. **Cancelar** = no se llama a nadie. **Confirmar** = una única llamada de coste mínimo.
6. Resultado correcto: etiqueta «IA REAL», «✔ procede de OpenAI (api.openai.com, respuesta resp_…)», tokens y coste estimado.
7. Para dejar de gastar: vuelve a poner `AMAZON_PRO_AI_ENABLE=0` y reinicia.

## Si hay un error
La app muestra una explicación en español (clave no aceptada, límite alcanzado, modelo no disponible, tiempo agotado…). Los errores 4xx no se cobran; en timeouts/5xx el consumo se marca como INCIERTO y se reserva el peor caso hasta que el admin lo concilie.

## Qué se registra
Solo estado, duración, tokens, coste estimado, modelo e id de respuesta (admin: `/api/ai/calls`). Nunca la clave, el prompt ni el texto de la respuesta.

## Límites honestos
No se ha hecho ninguna llamada real a OpenAI, ni se ha probado en un Windows real. Los nombres de campos de la respuesta y que los 4xx no facturen son supuestos hasta tu primera llamada. «IA REAL» solo se declara tras una respuesta con procedencia verificada.
