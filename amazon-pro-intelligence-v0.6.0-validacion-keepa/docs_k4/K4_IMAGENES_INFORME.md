# K4 · Informe de obtención de fotografías autorizadas
**Norma:** nada de scraping, capturas no autorizadas, imágenes generadas ni de productos similares. Una imagen solo se muestra con derecho de *visualizar* verificado; se exporta solo con derecho de *exportar* y copia local. Hoy **todas** las imágenes están «IMAGEN PENDIENTE DE VERIFICAR».
**Limitación honesta:** esta investigación usó fuentes secundarias y algunas son contradictorias; todo lo marcado «no verificado» debe confirmarse en la documentación oficial o con el titular antes de depender de ello. No se contrató ni consultó nada de pago.

| Fuente | Método | Términos / permisos (según lo hallado) | Visualizar · almacenar · exportar | Coste | Autorización necesaria |
|---|---|---|---|---|---|
| **Foto propia ACTIVCORE** (AHT) | Foto de estudio propia → registrar en K4 como FOTO_PROPIA_AHT | Es vuestra | Sí · sí · sí | 0 € | Ninguna (acta interna) |
| **Fabricante/titular de marca** (Kérastase, Nioxin, Redken, The Ordinary, Bio-Pilixin) | Solicitar por escrito permiso de uso de imagen oficial/pack-shot para comparativa interna | Lo fija el titular | Lo que conceda el permiso (pedir las tres) | 0 € (tiempo) | Permiso escrito → se registra con fecha de caducidad |
| **SP-API Catalog Items** | Imágenes por ASIN | Variantes completas solo a titulares de marca; para el resto, miniatura MAIN; aplican AUP/DPP de Amazon (no verificado) | Probable solo visualización; no redistribuir | Sin tarifa conocida (no verificado) | Aplicación registrada + OAuth; revisar AUP/DPP |
| **Amazon Creators/Associates API** (antes PA-API) | Enlaces/imágenes de afiliado | No almacenar/cachear imágenes; enlazar ≤24 h; puede exigir ventas calificadas por país (fuentes en conflicto) | Visualizar sí; almacenar y exportar **no** | 0 € si se cumple elegibilidad | Cuenta de afiliado elegible |
| **Keepa** | URLs de imagen que devuelve la API | No se encontraron términos que permitan reutilizarlas | Sin permiso por defecto | Tokens | **Desconocida** → consultar a Keepa por escrito; hasta entonces NO se usan |
| Captura/scraping de Amazon.es | — | Prohibido | No | — | **Descartado** |

## Ruta concreta recomendada
1. **Esta semana (0 €):** fotografiar ACTIVCORE (frontal, 50 mL, ficha) y registrarla (`Medios → FOTO_PROPIA_AHT`, ASIN propio, derechos visualizar/almacenar/exportar).
2. **Identificar el ASIN** de las 4 referencias que hoy no lo tienen (solo Kérastase lo tiene). Sin ASIN la vinculación exacta producto+variante+ASIN no es posible.
3. **Enviar solicitud de permiso** a cada marca (plantilla abajo). Al recibir respuesta: subir la imagen, registrar permiso y caducidad, verificar → pasa de PENDIENTE a VERIFICADA.
4. **Opcional (decisión tuya):** valorar SP-API Catalog para miniaturas MAIN si la AUP lo permite; pedir a Keepa por escrito sus términos de imagen.

## Plantilla de solicitud al titular
> Asunto: Solicitud de permiso de uso de imagen de producto — comparativa interna
> Somos AHT Advanced Hybrid Technologies S.L. Solicitamos autorización para usar la imagen oficial del producto [nombre, ASIN] en un análisis comparativo interno de mercado (visualización en una herramienta interna; sin venta ni publicidad). Indique si permite: visualizar, almacenar una copia, exportar a informes (PDF/PNG) y por cuánto tiempo, así como el crédito requerido. Quedamos a la espera de su respuesta escrita.
