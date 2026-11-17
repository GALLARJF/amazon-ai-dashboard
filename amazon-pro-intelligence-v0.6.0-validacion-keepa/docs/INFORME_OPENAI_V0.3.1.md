# Amazon Pro Intelligence V0.3.1 — Informe de compatibilidad con OpenAI

**Estado: preparada, NO activada.** No se ha usado ninguna credencial real, no se ha hecho ninguna llamada a `api.openai.com` (la suite de pruebas la prohíbe y lo verifica) y por tanto **no se declara «IA REAL»**. Las ejecuciones reales siguen **pendientes** de tu clave y autorización.

## 1. Inspección del adaptador `openai_compat` (V0.3)
| Hallazgo | Consecuencia |
|---|---|
| Usa `POST /v1/chat/completions` con `max_tokens` y mensaje `system` | La documentación oficial de modelos solo declara la **Responses API** para la familia GPT-6; no confirma Chat Completions para ellos. Además `max_tokens` no limita los tokens de razonamiento en modelos de razonamiento (el parámetro vigente es `max_output_tokens`, que **incluye razonamiento**). |
| Sin tarifas incorporadas (coste `null` si el operador no las da) | No se podía imponer un presupuesto real. |
| Sin presupuesto mensual ni registro de consumo | Solo había topes por ejecución. |
| Seguridad correcta: clave solo por entorno, HTTPS y host `api.openai.com`, doble consentimiento `ENABLE=1` | **Se conserva.** |

**Decisión:** `openai_compat` se mantiene intacto (sirve para servidores compatibles), pero se añade el proveedor **`openai`** (Responses API, `POST https://api.openai.com/v1/responses`). Petición: `model`, `instructions`, `input`, `max_output_tokens`, `store:false`, `reasoning.effort`; sin `temperature` ni `max_tokens`. Respuesta: se lee solo el ítem `message/output_text` (se ignora el razonamiento); `status=incomplete` se trata como error con consumo parcial registrado.

## 2. Modelos y tarifas oficiales (verificado 2026-11-16)
Fuentes oficiales: <https://developers.openai.com/api/docs/pricing> (antigüedad ~5 días al consultarla) y <https://developers.openai.com/api/docs/models>. USD por 1M tokens, tier *Standard*:

| ID API | Entrada | Entrada en caché | Salida | Contexto / máx. salida | Razonamiento |
|---|---|---|---|---|---|
| `gpt-6-luna` | 0,10 | 0,01 | 0,50 | 1,05M / 128K | none…max |
| `gpt-6.1-terra` | 1,00 | 0,05 | 5,00 | 1,05M / 128K | none…max |
| `gpt-6.1-sol` | 2,00 | 0,10 | 10,00 | 1,05M / 128K | low…max |
| `gpt-6-astra` | 10,00 | 1,00 | 50,00 | 1,05M / 128K | low…max |

Notas oficiales: el endpoint regional (residencia de datos) y FedRAMP añaden +10 %; la página tiene pestaña Flex/Batch con precios menores (no verificados como descuento, **no se usan**); hay una nota de precio promocional de «GPT-5.6 Sol» hasta el 30-nov-2026 que la página no concilia con la tabla (el nombre difiere de `gpt-6.1-sol`): **se usa el precio de la tabla**. Recargo por contexto largo (>272K tokens) existe según agregadores, **irrelevante aquí** (prompts ≈ 1,3K tokens). Páginas de terceros se consultaron solo como contraste y **no** se usan como fuente.

**No verificado (requiere tu clave):** que tu cuenta/tier tenga acceso a estos IDs (`tools/check_openai_models.py --yes`, sin coste de generación) y los nombres exactos de los campos de uso (`usage.input_tokens/output_tokens`, `output_tokens_details.reasoning_tokens`): están implementados según el formato estándar de la Responses API, el parseo es defensivo y, si faltan, se contabiliza el **peor caso**. Se confirmará en la primera llamada real.

## 3. Recomendación
- **Tareas habituales → `gpt-6-luna`** (perfil `economico`, por defecto). Es el más barato, descrito por OpenAI como el eficiente para tareas enfocadas y de alto volumen, y el Director solo redacta una síntesis de hechos ya calculados (los cálculos son deterministas). ≈ **0,0004 USD** por ejecución típica.
- **Razonamiento complejo → `gpt-6.1-sol`** (perfil `razonamiento`): OpenAI lo describe como casi al nivel de Astra a menor coste; 20× el precio de Luna en entrada y en salida, ≈ **0,009 USD** por ejecución típica.
- `gpt-6-astra` (perfil `maximo`) solo bajo orden expresa: su peor caso (≈ 0,138 USD) **supera el tope por ejecución por defecto (0,05)** y la app lo bloquea hasta que subas `AMAZON_PRO_AI_MAX_COST`. No lo recomiendo para este uso.
- `gpt-6.1-terra` queda como intermedio si Luna resultara insuficiente.

## 4. Configuración segura (ver `config/openai.env.example`)
Clave solo en `OPENAI_API_KEY` (entorno del servidor; no se envía al navegador, ni se registra, ni aparece en errores; el estado público devuelve solo `key_present`). Doble consentimiento `AMAZON_PRO_AI_ENABLE=1`. Solo `https://api.openai.com` (otros hosts bloqueados; loopback solo con `ALLOW_LOOPBACK=1` para pruebas). `store:false`. Los cuerpos de error HTTP no se registran.

**Límites** (todos se evalúan **antes** de llamar; un rechazo no genera tráfico):
| Variable | Defecto | Función |
|---|---|---|
| `AMAZON_PRO_AI_MAX_IN` | 12000 | tokens de entrada estimados |
| `AMAZON_PRO_AI_MAX_OUT` | 2500 | salida **incluido razonamiento** (`max_output_tokens`) |
| `AMAZON_PRO_AI_MAX_COST` | 0,05 USD | peor caso por ejecución = entrada estimada + salida máxima |
| `AMAZON_PRO_AI_MONTHLY_BUDGET` | **obligatorio** | gasto REAL del mes + peor caso ≤ presupuesto |
| tarifa | tabla oficial | modelo sin tarifa y sin `PRICE_IN/OUT` → no se llama (`PRECIO_DESCONOCIDO`) |

**Registro de consumo:** cada intento queda como `ai_run` (modelo, modo, inicio/fin, duración, tokens y su origen, tokens de razonamiento, coste estimado y fuente de tarifa, hechos consultados con hash del expediente, anclaje, evidencias, límites, error). `GET /api/ai/usage` (solo admin) suma el mes en curso por modelo y cuenta; la UI muestra «gasto real del mes X / presupuesto». **Solo cuentan las ejecuciones en modo REAL**; SIMULADA y PRUEBA_LOCAL no. Límite honesto: el coste es una **estimación** (tokens × tarifa de lista, sin descuento de caché); un timeout de red puede haber generado coste no visible. La factura/panel de OpenAI manda; configura allí también un límite mensual.

## 5. Prueba extremo a extremo PHIVITAL MAGNESIO (sin consumo real)
`tests/openai_test.py` + `demos/run_e2e_openai.py` (servidor local que imita la Responses API; `demos/e2e_phivital_openai.json`):
- Plantilla real PHIVITAL (INCOMPLETO) → 7 coworkers ejecutados y registrados → motor determinista: **REVISAR** → solo entonces el Director construye el prompt con hechos `[F#]` (resultados de los coworkers y del motor, sin datos externos) → adaptador `openai` → respuesta.
- Modo registrado **PRUEBA_LOCAL**, nunca REAL; `real_verified=false`; gasto real contabilizado: 0.
- Cifra inventada («777 ventas») → respuesta **descartada** → resumen determinista «SIN IA». Error HTTP 429, respuesta vacía e incompleta → «SIN IA» con motivo; la incompleta registra el consumo parcial. Los datos ausentes figuran como hechos (pendientes).
- Medido: prompt ≈ 1.296 tokens (chars/4).

## 6. Presupuesto estimado de pruebas reales (cuando autorices)
| Modelo | Típica* | Peor caso |
|---|---|---|
| `gpt-6-luna` | 0,00043 USD | 0,00138 USD |
| `gpt-6.1-sol` | 0,0086 USD | 0,0276 USD |
| `gpt-6-astra` | 0,043 USD | 0,138 USD (bloqueado por tope) |

\*salida típica **supuesta** de 600 tokens incl. razonamiento (no medida). Plan de pruebas propuesto: 10 ejecuciones Luna + 5 Sol = **≈ 0,05 USD típico, ≤ 0,15 USD en el peor caso**. Presupuesto mensual recomendado para el arranque: **2 USD** (`MONTHLY_BUDGET=2`, `MAX_COST=0.02`).

## 7. Resultados de pruebas (sin consumo real)
Detalle en `tests/resultado_ejecucion_final.txt`: JS 11+21+29+16, paridad 657/657, store 17, backend 51, **OpenAI 50**, ámbito 6, API 51, seguridad 53, esquema, UI 40. V0.1, V0.2 y V0.3 verificadas sin alteración (`docs/evidencia_integridad_V01_V02_V03.txt`). AHT Executive Neon no modificado; interfaz horizontal NEON conservada (solo cambia la etiqueta de versión y la línea de estado del Director).

## 8. Pendiente / bloqueos
1. Clave y autorización de gasto (única vía para la primera ejecución REAL). 2. Confirmar IDs accesibles y campos de uso en la primera llamada. 3. Datos documentados del piloto PHIVITAL (costes, CSV, keywords, regulatorio) y titular legal «POR CONFIRMAR»: sin ellos el expediente seguirá en REVISAR con o sin IA. 4. Ningún coworker se declara operativo mientras sus datos no sean de origen USUARIO y completos.
