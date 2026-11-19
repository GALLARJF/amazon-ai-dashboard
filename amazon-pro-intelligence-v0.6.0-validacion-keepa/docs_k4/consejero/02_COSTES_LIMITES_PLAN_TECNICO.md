# Consejero Estratégico — costes, límites y plan técnico
Nada de esto está activado. Cada fase exige tu aprobación expresa antes de gastar.

## 1. Modelo de costes (parametrizado; sin inventar tarifas)
Coste de una investigación = Σ(tokens × tarifa del proveedor) + llamadas de búsqueda/lectura + (opcional) Keepa. Las tarifas las fija el operador; `ai.py` ya impide llamar sin tarifa conocida.
Ejemplo ORIENTATIVO con las tarifas OFICIALES registradas en el código (`ai.PRICES`, verificadas por el sistema el 2026-11-16, **no re-verificadas hoy**), para una investigación tipo «ACTIVCORE» de ~120 000 tokens de entrada (lecturas de ~12 fuentes + libro de evidencias) y ~25 000 de salida (razonamiento + informe):
| Perfil (modelo) | Entrada | Salida | Total estimado |
|---|---|---|---|
| económico (gpt-6-luna) | 0,012 USD | 0,0125 USD | ≈ 0,03 USD |
| razonamiento (gpt-6.1-sol) | 0,24 USD | 0,25 USD | ≈ 0,49 USD |
| máximo (gpt-6-astra) | 1,20 USD | 1,25 USD | ≈ 2,45 USD |
Más: verificador (segunda pasada, ≈ +40 %), búsqueda web (**coste de proveedor de búsqueda no verificado**; hay opciones gratuitas con límite y de pago), y 0 tokens Keepa salvo autorización. Orden de magnitud realista: **0,5–5 USD por investigación profunda**, 10–50 USD/mes con 10 investigaciones.

## 2. Límites propuestos (por defecto)
- Tope por investigación: 3 USD; tope mensual: 30 USD; ambos ajustables SOLO por admin y auditados.
- Cada investigación muestra antes: preguntas, herramientas, tokens y coste máximo → aprobación (Ops N2).
- Primera ejecución real solo sobre ACTIVCORE (caso de evaluación) y con tope 1 USD.
- Parada de emergencia y kill switch heredados; coste inesperado → bloquea y avisa.
- Listas de hosts permitidos por herramienta; sin POST a terceros; sin credenciales en el modelo; ningún envío de datos de ventas a buscadores.
- Datos propios sensibles (costes, ventas) no se envían al proveedor salvo decisión expresa; por defecto se envían solo agregados o rangos.

## 3. Permisos y cumplimiento
Scraping de Amazon y de reseñas: **excluido**. Brand Analytics/Customer Feedback/Ads: requieren Brand Registry/autorización de vendedor (por verificar en documentación oficial antes de activar). Fuentes con derechos de autor: citas ≤ 15 palabras y enlace; el libro de evidencias guarda extractos mínimos y hash, no copias completas.

## 4. Plan técnico por fases
| Fase | Entregable | Gasto | Criterio de salida |
|---|---|---|---|
| F0 (hecho) | Planificador, contrato de evidencias, `ai.py` con presupuesto | 0 | — |
| F1 | Interfaces `ProveedorLLM/Busqueda/Lectura`; adaptador mock determinista; libro de evidencias externo (tabla `k4_evidencia`) | 0 | tests de contrato verdes con mocks |
| F2 | Planificador de investigación (árbol de hipótesis) y informe de 10 apartados con esquema JSON; verificador de citas y cifras | 0 (mock) | las pruebas anti-plantilla (doc 03) corren con mock y fallan correctamente ante trampas |
| F3 | Adaptador real de búsqueda/lectura (solo hosts permitidos) + 1.er proveedor LLM | ≤ 1 USD (aprobado) | caso ACTIVCORE reproducido con evidencias verificadas |
| F4 | 2.º proveedor LLM como verificador independiente; comparación entre proveedores | ≤ 3 USD | el verificador detecta ≥ 90 % de las trampas |
| F5 | Registro de predicciones y puntuación posterior; integración con seguimiento | 0 | primeros 30 días medidos |
| F6 | (Si AHT autoriza) SP-API/Brand Analytics/Ads | por verificar | datos reales sustituyen hipótesis |

## 5. Decisiones que necesito de ti para empezar F1–F2 (0 €)
1. Confirmar la arquitectura (sin proveedor único).
2. Autorizar F1–F2 (sin llamadas externas).
3. Más adelante, para F3: proveedor LLM, clave en Render (la pones tú) y topes.
