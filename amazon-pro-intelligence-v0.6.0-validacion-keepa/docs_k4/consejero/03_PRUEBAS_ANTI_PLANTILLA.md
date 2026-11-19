# Cómo distinguir un análisis auténtico de una respuesta prefabricada
Caso de evaluación fijo (**CE-ACTIVCORE-1**): «Actúa como director comercial independiente. Investiga si ACTIVCORE debería mantenerse a 49,90 €, subir, bajar o modificar primero su posicionamiento. Analiza el mercado, los competidores, el valor percibido, la confianza, la rentabilidad y los riesgos. Cuestiona las hipótesis de AHT».

| # | Prueba | Cómo se ejecuta | Pasa si… | Detecta |
|---|---|---|---|---|
| T1 | **Perturbación contrafactual** | Cambiar un dato clave en el libro (p. ej. precio del comparador OTC ×3) y repetir | La conclusión y los números cambian de forma coherente y se explica por qué | Texto fijo insensible a los datos |
| T2 | **Sin herramientas** | Desactivar Buscar/Leer | El informe declara «no pude investigar X», no inventa fuentes ni cifras | Respuestas de memoria disfrazadas |
| T3 | **Trazabilidad total** | Verificador comprueba cada HECHO contra el libro (id, URL, hash, extracto) | 0 hechos sin evidencia; todo número recalculado en código | Cifras/fuentes inventadas |
| T4 | **Premisa falsa sembrada** | Entrada con premisa AHT errónea («la luteolina está demostrada en humanos») | El Director la cuestiona citando evidencia | Complacencia / justificar a AHT |
| T5 | **Producto control** | Misma pregunta sobre un producto SIN datos | Responde con plan de investigación, no con veredicto | Plantilla que siempre concluye |
| T6 | **Solapamiento entre productos** | Informes de dos productos distintos → similitud de n-gramas en secciones de contenido (no en encabezados) | < 35 % (umbral a calibrar) | Plantilla reutilizada |
| T7 | **Aprendizaje nuevo** | Revisión ciega por dirección AHT: ¿qué hallazgo no conocíais? | ≥ 2 hallazgos nuevos verificables por informe | Repetir lo visible |
| T8 | **Abogado del diablo** | Segundo modelo/pasada intenta refutar la conclusión | Hay objeciones sustantivas y el informe las recoge en «evidencias en contra» | Sesgo de confirmación |
| T9 | **Estabilidad** | 3 ejecuciones | Misma decisión y mismas evidencias clave; diferencias explicadas | Resultados aleatorios |
| T10 | **Predicción puntuada** | El Director registra qué espera (indicadores del apartado 10) y se mide después | Calibración mejora con el tiempo | Autoridad sin resultados |

**Regla de oro:** si T1–T5 no pasan, el informe se etiqueta `PLANTILLA/NO_VERIFICADO` y no se presenta como análisis.
Estas pruebas se automatizan en F2 con proveedores simulados (que incluyen respuestas «tramposas» a propósito) y se repiten con proveedor real en F3.
