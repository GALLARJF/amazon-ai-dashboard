# Manual de Sergio — Amazon Pro Intelligence V1.0 (candidata)

> Estado honesto: esta versión es una **candidata**, no producción. Funciona con datos locales, informes CSV importados y los datos reales de Keepa ya guardados. **Amazon SP-API, Ads API, OpenAI y Keepa nuevo NO están conectados.** Ejecutada y probada solo en Linux; **en Windows no está verificada** (ver INSTALACION_V100.md).

## 1. Entrar
1. Abre la aplicación con `INICIAR.bat` (doble clic). Se abre el navegador.
2. Pulsa **Entrar** e inicia sesión con tu usuario. Si no recuerdas la contraseña de `admin`, usa `RESTABLECER_ADMIN.bat`.

## 2. Las cinco secciones
- **INICIO** — resumen: qué hay, qué falta y qué es real o simulado.
- **LANZAMIENTOS** — prepara un producto para lanzarlo. Por defecto aparece **ACTIVCORE**.
- **MIS VENTAS** — resultados a partir de los informes de Amazon que **tú importas** (CSV).
- **PRODUCTOS** — catálogo y fichas de producto.
- **DIRECTOR IA** — qué toca hacer ahora, quién lo hace y qué está bloqueado.

## 3. Preparar y lanzar un producto (LANZAMIENTOS)
1. Elige el producto. Verás el **veredicto**. Hoy, para ACTIVCORE, es **NO DECIDIBLE**: faltan datos. La plataforma **nunca dice GO** si faltan evidencias.
2. Revisa los **20 competidores de Keepa** (precio, fecha del precio y fuente). Cada fila indica REAL y **comparabilidad NO CONFIRMADA** hasta que alguien la confirme a mano.
3. Mira los **desbloqueos**: cada uno dice qué hay que aportar, quién y cuánto cuesta. Esa es tu lista de trabajo.
4. Descarga el expediente (Markdown/JSON) o los competidores (CSV, HTML o Markdown) desde los enlaces de descarga.

## 4. Vender y optimizar (MIS VENTAS)
1. Descarga de Seller Central tus informes de **ventas** y de **publicidad** (CSV).
2. Impórtalos. Se guardan **sin modificar** (con huella SHA-256) y se marcan **IMPORTADO**: no son una conexión con Amazon.
3. La app calcula ventas, unidades, conversión, **ACOS** y **TACoS**. Si no hay informes muestra **SIN DATOS**, nunca ceros. El mismo informe no se puede importar dos veces.
4. TACoS solo vale si los periodos de ventas y publicidad coinciden.

## 5. Economía
El motor calcula contribución por unidad, ACoS de equilibrio, escenarios (pesimista/base/optimista) y sensibilidad. **Si falta un coste, dice NO CALCULABLE y qué falta** — no inventa números. Los volúmenes y costes fijos son hipótesis tuyas.

## 6. Director IA
Muestra los especialistas (mercado, finanzas, regulatorio, listing, publicidad, operaciones), en qué orden trabajan, quién los desbloquea y cuánto cuesta. **Nada se ejecuta solo**: las acciones con coste requieren tu aprobación.

## 7. Cómo leer las etiquetas
| Etiqueta | Significa |
|---|---|
| REAL | dato obtenido de Keepa y guardado con fuente y fecha |
| IMPORTADO | informe de Amazon que importaste |
| CALCULADO | resultado de una fórmula con datos anteriores |
| HIPÓTESIS / SIMULADO | supuesto o prueba; **no es real** |
| SIN DATOS / NO CALCULABLE | falta información; no se rellena |
| NO CONFIRMADO / OBSOLETO | pendiente de revisión humana / precio antiguo |

## 8. Qué NO hace
No publica productos, no crea campañas, no toca Amazon, no gasta en Keepa ni en OpenAI por sí sola.

## 9. Si algo falla
- No arranca: lee el mensaje de la ventana negra (suele faltar Python).
- Base de datos dañada: la app **se niega a arrancar sin tocarla**; restaura un respaldo (ver INSTALACION_V100.md).
- Lo que necesita tu decisión está en `FICHA_INTEGRACIONES_V100.md`.
