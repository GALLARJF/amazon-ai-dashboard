# No puedo iniciar sesión: restablecer la contraseña de admin (Windows)

## Por qué pasa
La contraseña de `admin` se muestra en la ventana negra **solo la primera vez** que la app crea su base de datos. Si ya existía la base (`data\amazon_pro.db`), al arrancar solo ves el «token de administrador de conectores» (otra cosa, no sirve para entrar). Las contraseñas no se guardan en claro, así que no se pueden «recuperar»: se restablece una nueva.

## Pasos (2 minutos, sin programar)
1. **Cierra** la ventana negra de `INICIAR.bat` (si está abierta).
2. En la carpeta de la app (la MISMA donde usabas la app), haz doble clic en **`RESTABLECER_ADMIN.bat`**.
3. Escribe una contraseña nueva (mínimo 10 caracteres; no se ve al escribir) y repítela. *Si prefieres que la genere el programa, pulsa solo ENTER: te la muestra una vez, apúntala.*
4. Verás «LISTO». Abre `INICIAR.bat` e inicia sesión con usuario `admin` y la contraseña nueva.

## Qué hace y qué NO hace
- Hace antes una **copia de seguridad** en `data\copias\`.
- Cambia **solo** la contraseña de `admin` y cierra las sesiones abiertas.
- **No toca** expedientes, cuentas, otros usuarios ni `ai.env` (tu clave de OpenAI).
- **No desactiva** el inicio de sesión. Queda anotado en la auditoría (sin contraseña).

## Si algo sale distinto
- «No encuentro la base de datos»: ejecuta `RESTABLECER_ADMIN.bat` desde la carpeta donde usabas la app. Importante: cada carpeta de versión tiene su propia `data\`. Si descomprimiste una versión nueva, tus expedientes siguen en la carpeta antigua; copia `data\amazon_pro.db` a la nueva `data\` (con la app cerrada).
- «La aplicación está abierta»: cierra la ventana de `INICIAR.bat`.
- Para volver atrás: copia el archivo de `data\copias\` sobre `data\amazon_pro.db`.
