@echo off
setlocal
title Amazon Pro Intelligence
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
%PY% tools\lanzador.py
if errorlevel 1 (
  echo.
  echo  La aplicacion no pudo arrancar. Lee el mensaje de arriba.
)
pause
