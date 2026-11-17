@echo off
setlocal
title Amazon Pro Intelligence - Configurar clave de Keepa
set "CARPETA=%USERPROFILE%\AmazonPro"
set "ARCHIVO=%CARPETA%\keepa.env"
if not exist "%CARPETA%" mkdir "%CARPETA%"
if not exist "%ARCHIVO%" copy "%~dp0config\keepa.env.plantilla" "%ARCHIVO%" >nul
echo.
echo  ============================================================
echo   Se va a abrir el Bloc de notas con el archivo de Keepa:
echo   %ARCHIVO%
echo  ============================================================
echo.
echo   1) Sustituye PEGA_AQUI_TU_CLAVE_KEEPA por tu clave (Ctrl+V). Sin comillas ni espacios.
echo   2) Deja AMAZON_PRO_KEEPA_ENABLE=0 hasta que quieras consultar Keepa (consume tokens).
echo      Para consultar: cambialo a 1, guarda y reinicia la aplicacion (INICIAR.bat).
echo   3) Guarda (Ctrl+G) y cierra el Bloc de notas.
echo.
echo   IMPORTANTE: no envies este archivo a nadie ni pegues la clave en ningun chat.
echo.
pause
notepad "%ARCHIVO%"
echo.
echo  Listo. Arranca la aplicacion con INICIAR.bat: en la consola veras si Keepa esta DESACTIVADO o HABILITADO.
pause
