# Dónde pegar tu clave de OpenAI (Windows) — 4 pasos, sin programar

**La clave NO va en el código, NO va en GitHub y NO la escribes en el chat.** Va en un archivo de texto en TU carpeta de usuario, fuera de este proyecto:

`C:\Users\TU_USUARIO\AmazonPro\ai.env`

*(El archivo no existe hasta que hagas el paso 2: el programa lo crea por ti.)*

## Antes de empezar (solo la primera vez)
Necesitas **Python** instalado. Si no lo tienes: entra en https://www.python.org/downloads/ → descarga → al instalar **marca la casilla «Add python.exe to PATH»**.

## Paso 1 — Descomprime
Descomprime el ZIP en una carpeta, por ejemplo en el Escritorio. Entra en la carpeta `amazon-pro-intelligence-v0.3.4`.

## Paso 2 — Haz doble clic en `CONFIGURAR_CLAVE.bat`
Se abrirá el **Bloc de notas** con el archivo `ai.env`. Verás esta línea:

```
OPENAI_API_KEY=PEGA_AQUI_TU_CLAVE
```

## Paso 3 — Pega la clave ahí
- Borra `PEGA_AQUI_TU_CLAVE` y pega tu clave con **Ctrl+V**, justo después del `=`.
- Debe quedar así (con tu clave real, que empieza por `sk-`):
  `OPENAI_API_KEY=sk-........`
- **Sin comillas, sin espacios, todo en la misma línea.**
- **No toques** la línea `AMAZON_PRO_AI_ENABLE=0`. Con el `0` la IA **no hace ninguna llamada y no cuesta nada**.
- Guarda con **Ctrl+G** y cierra el Bloc de notas.

## Paso 4 — Comprueba que está bien (no gasta nada)
Haz doble clic en `VERIFICAR_CONFIGURACION.bat`. Debe decir:
- «Clave presente: SÍ · formato: reconocible»
- «IA DESHABILITADA» ← es lo correcto por ahora
- «NO se conecta a internet y NO gasta nada»

Si dice «formato NO reconocible», vuelve al paso 3: seguramente hay un espacio o unas comillas de más.

## Usar la aplicación
Doble clic en `INICIAR.bat`. Se abre en tu navegador (`http://localhost:8765`). La primera vez aparece en la ventana negra el usuario `admin` y su contraseña: **apúntala**, solo se muestra una vez.

---
## Seguridad (léelo una vez)
- No envíes `ai.env` por correo ni lo pegues en ningún chat. Si lo hicieras, **borra esa clave en el panel de OpenAI y crea otra**.
- Este proyecto lleva un `.gitignore` que impide subir `ai.env` o cualquier `.env` a GitHub, y el archivo ni siquiera está dentro de la carpeta del proyecto.
- En el panel de OpenAI, pon un **límite de gasto mensual** (p. ej. 5 €) como segunda barrera. La aplicación ya trae el suyo: **2 USD/mes y 0,02 USD por consulta**.

## Más adelante, cuando TÚ decidas autorizar el gasto
Solo entonces: abre otra vez `CONFIGURAR_CLAVE.bat`, cambia `AMAZON_PRO_AI_ENABLE=0` por `AMAZON_PRO_AI_ENABLE=1`, guarda, y ejecuta `VERIFICAR_CONFIGURACION.bat` (debe decir «LISTO PARA LLAMAR»). La primera llamada solo puede hacerse con el expediente de PRUEBA sintético (sin datos reales). Detalle en `docs/ACTIVAR_API_OPENAI.md`.
