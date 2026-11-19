# K4 · Fotografías auténticas: opciones técnicas y permitidas (investigación)
Fecha: 2026-11-19. **No es asesoramiento legal.** Lo que sigue distingue lo comprobado en fuentes de lo que debe confirmar AHT/asesoría. El sistema implementado hace cumplir la política *por operación* (mostrar · almacenar · transformar · exportar · redistribuir) y por defecto no permite nada que no conste con evidencia.

## 1. Hallazgos de la investigación
| Hecho | Fuente | Fiabilidad |
|---|---|---|
| El cliente de la API de Keepa expone campos de imagen del producto (p. ej. `imagesCSV`) y su documentación no es una licencia de uso de esas fotos | documentación de campos en wrappers de Keepa (developer.sellerassistant.app, keepaapi.readthedocs.io) | Existe el dato; **términos de Keepa sobre uso/almacenamiento de imágenes: NO ENCONTRADOS en fuente primaria** |
| Amazon Associates: las imágenes (Program Content) deben obtenerse mediante la API oficial (Product Advertising API, hoy Creators API) y no por scraping | resumen de políticas (tidyplugins, getlasso) y acuerdo de operación (affiliate-program.amazon.com) | Secundaria + primaria parcial |
| Associates: **no se pueden almacenar ni cachear imágenes de Product Advertising Content**; solo se puede guardar un enlace hasta 24 h; una aplicación cliente no puede cachear ese contenido | cita de las *Associates Program Policies* recogida por conductatlas.com (actualizada 2026-05-20) | Secundaria (cita literal de política); verificar en el texto oficial |
| La Creators API de Amazon devuelve las imágenes como URLs de `m.media-amazon.com` con varios tamaños (small/medium/large) y variantes | affiliate-program.amazon.com/creatorsapi/docs (referencia de recursos «images») | Primaria |
| El contenido de Amazon Associates excluye datos/imágenes de ofertas de otros sitios | acuerdo de operación | Primaria |
| SP-API: sujeto a Acceptable Use Policy, Data Protection Policy y Developer Agreement (vendedor propio) | developer-docs.amazon.com/sp-api/docs/policies-and-agreements | Primaria (existencia de políticas; el detalle sobre imágenes de terceros no se ha leído) |
Conclusión: **almacenar copias locales de fotos de competidores obtenidas de Amazon/Keepa debe considerarse NO permitido** salvo autorización escrita; la vía de Amazon para mostrar imágenes es por enlace/CDN a través de su API oficial, con límites de caché.

## 2. Opciones evaluadas
| # | Opción | Visualizar | Almacenar local | Transformar | Exportar PDF/PNG | Redistribuir | Viabilidad y condición | Estado en K4 |
|---|---|---|---|---|---|---|---|---|
| 1 | **Fotos propias de AHT** (ACTIVCORE, PhiVital, elixir) | Sí | Sí | Sí | Sí | Sí (AHT es titular) | Inmediata: AHT sube JPG/PNG. Derechos = titular AHT | **IMPLEMENTADO** (subida con registro) |
| 2 | **Fotos del fabricante con autorización escrita** (prensa/catálogo/distribuidor) | Según licencia | Según licencia | Según licencia | Según licencia | Rara vez | Pedir al fabricante/prensa: licencia que cubra «comparativa interna + informe a dirección». Guardar la autorización como evidencia | **IMPLEMENTADO** (permisos por operación + evidencia obligatoria) |
| 3 | **Catálogo propio vía SP-API Catalog Items** (productos de AHT) | Sí | Para uso propio, sujeto a AUP/DPP | Sí | Sí (propio) | — | Requiere credenciales SP-API de AHT | Adaptador **NO OPERATIVO** |
| 4 | **Visualización remota (hot-link) de imágenes de Amazon vía API oficial** (Creators API/PA-API) | **Posible** si AHT cumple las condiciones del programa | **No** (solo enlace ≤ 24 h) | No | **No** | No | Requiere cuenta Associates y revisar si un panel interno privado cuenta como «sitio» autorizado; **requiere ampliar la CSP (`img-src m.media-amazon.com`)**, decisión de seguridad que no tomo sin aprobación | Modelo y política listos (modo `ENLACE_REMOTO`, TTL 24 h, sin copia); **desactivado** y CSP intacta |
| 5 | **Imágenes de Keepa (`imagesCSV`) por enlace** | Dependiente de términos de Keepa **no localizados** | Desconocido ⇒ No | Desconocido ⇒ No | Desconocido ⇒ No | No | Solicitar a Keepa (soporte) confirmación escrita; coste de tokens ya cubierto por `/product` | Campo previsto; **sin permiso por defecto** |
| 6 | **Subida manual con derecho acreditado** (p. ej. foto tomada por AHT de un producto comprado) | Sí | Sí | Sí | Sí si se acredita | No | Fotografiar un producto adquirido legítimamente: AHT es autor de la foto; el diseño del envase es marca del tercero ⇒ uso comparativo interno razonable, **confirmar con asesoría para exportación externa** | **IMPLEMENTADO** (origen `FOTO_PROPIA_DE_PRODUCTO_AJENO`) |
| 7 | Scraping de la página de producto / buscadores / «imágenes similares» / IA generativa | — | — | — | — | — | **Prohibido** | Bloqueado por diseño |
**Camino recomendado para tener comparativa con envases reales ya:** (a) fotos propias de ACTIVCORE; (b) AHT compra o recibe una unidad de cada competidor y la **fotografía** (opción 6) — da imagen auténtica, vinculada a ASIN/variante, de uso interno; (c) en paralelo solicitar licencias (opción 2) y confirmación de Keepa (opción 5) para la exportación externa. La opción 4 se activa solo si AHT aprueba la CSP y confirma la elegibilidad Associates.

## 3. Qué se implementa (iteración 1)
- Registro `k4_media` con **vinculación exacta**: `product_id` + `variante` (frontal/lateral/caja/dorso) + `asin` + `pais` + `volumen_ml`; una imagen se rechaza si su ASIN/volumen no coincide con el competidor al que se vincula, y no puede vincularse a dos ASIN.
- **Procedencia**: origen, fuente, URL/referencia, fecha de captura, autor/titular, hash SHA-256 y bytes, quién subió y cuándo.
- **Derechos por operación** (`mostrar`, `almacenar`, `transformar`, `exportar`, `redistribuir`) cada uno `true/false`, con `licencia`, `evidencia_ref` y caducidad; sin evidencia ⇒ todo `false`. Solo `admin/approver` pueden verificar derechos.
- Estados: PENDIENTE → VERIFICADA / RECHAZADA; una imagen solo se sirve si VERIFICADA y con el permiso de la operación pedida (`mostrar` en pantalla, `exportar` en PDF/PNG).
- Almacenamiento local en `/data/media/<sha256>.<ext>` **solo si `almacenar=true`**; si no, no se guarda el binario (solo metadatos/enlace).
- Para cada competidor sin fuente autorizada: marcador «IMAGEN PENDIENTE DE VERIFICAR» **más la autorización que falta** (p. ej. «Falta: foto propia o licencia del fabricante; Keepa/Amazon no permiten almacenar»).
- Exportación PDF/PNG: omite imágenes sin `exportar`, lo declara en el documento y registra cada exportación en la auditoría.

## 4. Decisiones que necesito de AHT (imágenes)
I1 Fotografiar una unidad de cada competidor (opción 6) · I2 solicitar licencias a fabricantes (opción 2) · I3 consulta escrita a Keepa sobre `imagesCSV` · I4 ¿tiene AHT cuenta Associates? y ¿se aprueba ampliar la CSP para hot-link (opción 4)? · I5 revisión legal de exportación externa.
