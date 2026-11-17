@echo off
setlocal
title Amazon Pro Intelligence - Configurar clave de OpenAI
set "CARPETA=%USERPROFILE%\AmazonPro"
set "ARCHIVO=%CARPETA%\ai.env"
if not exist "%CARPETA%" mkdir "%CARPETA%"
if not exist "%ARCHIVO%" copy "%~dp0config\ai.env.plantilla" "%ARCHIVO%" >nul
echo.
echo  ============================================================
echo   Se va a abrir el Bloc de notas con el archivo de la clave:
echo   %ARCHIVO%
echo  ============================================================
echo.
echo   1) Busca la linea que dice:  OPENAI_API_KEY=PEGA_AQUI_TU_CLAVE
echo   2) Borra PEGA_AQUI_TU_CLAVE y pega tu clave (Ctrl+V) en su lugar.
echo      Sin comillas, sin espacios, en la misma linea, justo despues del =
echo   3) Deja AMAZON_PRO_AI_ENABLE=0 (asi NO se gasta nada todavia).
echo   4) Guarda (Ctrl+G) y cierra el Bloc de notas.
echo.
echo   IMPORTANTE: no envies este archivo a nadie ni pegues la clave en ningun chat.
echo.
pause
notepad "%ARCHIVO%"
echo.
echo  Listo. Ahora haz doble clic en VERIFICAR_CONFIGURACION.bat
pause
