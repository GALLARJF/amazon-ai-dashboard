@echo off
setlocal
cd /d "%~dp0"
echo.
echo  Creando el acceso directo "AHT Amazon Pro Intelligence" en el Escritorio...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\crear_acceso_directo.ps1" -Carpeta "%~dp0"
if errorlevel 1 (
  echo.
  echo  No se pudo crear el acceso directo. Puedes arrancar la aplicacion con INICIAR.bat.
  pause
  exit /b 1
)
echo.
echo  Listo. Haz doble clic en el icono "AHT Amazon Pro Intelligence" del Escritorio.
pause
