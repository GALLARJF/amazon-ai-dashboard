@echo off
setlocal
title Amazon Pro Intelligence - Verificar configuracion (sin gastar nada)
cd /d "%~dp0"
set "PY="
python --version >nul 2>&1 && set "PY=python"
if not defined PY py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY (
  echo  No se encuentra Python. Instalalo desde https://www.python.org/downloads/
  echo  y marca la casilla "Add python.exe to PATH" durante la instalacion.
  pause
  exit /b 1
)
echo.
echo  Esta comprobacion NO se conecta a internet y NO gasta nada.
echo.
%PY% tools\preflight_primera_llamada.py
echo.
pause
