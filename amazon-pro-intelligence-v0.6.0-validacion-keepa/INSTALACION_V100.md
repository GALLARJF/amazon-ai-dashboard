# Instalación y operación — Amazon Pro Intelligence V1.0 (candidata)

## Requisitos
- Python 3.10 o superior (en Windows, marca «Add python.exe to PATH»).
- Solo biblioteca estándar para ejecutar la aplicación. Para las pruebas de interfaz: `pip install playwright` y `playwright install chromium`.

## Arranque
- **Windows:** doble clic en `INICIAR.bat`. *(No verificado en Windows: la V1.0 se ha probado solo en Linux. Si falla, envía el mensaje de la ventana.)*
- **Linux/macOS:** `python3 server.py 8765` y abre `http://localhost:8765`.

## Credenciales
Se guardan **solo en ficheros locales** (`ai.env`, `keepa.env`, y para SP-API/Ads los `.env` de la ficha), nunca en GitHub, Drive ni chat. Sin ellos la app funciona en modo local sin gasto.

## Datos y copias de seguridad
- Base de datos: `data/amazon_pro.db`.
- Copia: función `respaldar` (backend/respaldo100.py) → fichero `.db` + `.sha256`. Restaurar: `restaurar`, que verifica hash, integridad y cadena de auditoría y conserva copia del estado previo.
- Con la base dañada la aplicación **no arranca** y no la modifica.

## Pruebas
`bash tests/run_all.sh` ejecuta toda la batería (unitarias, integración, extremo a extremo, persistencia, concurrencia, seguridad, regresión y Chromium real). Termina con «TODAS LAS SUITES OK» solo si todo pasa.

## Desarrollo autónomo
Sesiones independientes programadas **cada 4 horas** (no es ejecución continua). Un bloqueo en la rama `aht-autonomia-estado` impide que dos sesiones trabajen a la vez; para detenerlas, crea el fichero PARAR en esa rama.

## Límites vigentes
0 € de gasto adicional, 0 tokens nuevos de Keepa, ninguna API de pago, ninguna publicación en Amazon, sin despliegue a producción.
