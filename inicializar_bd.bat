@echo off
chcp 65001 >nul
title Panadería El Ranchero — Inicializar Base de Datos

echo.
echo  =====================================================
echo    Panaderia El Ranchero — Inicializar Base de Datos
echo  =====================================================
echo.

REM Cambiar al directorio donde está este .bat
cd /d "%~dp0"

REM Verificar que Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python no esta instalado o no esta en el PATH.
    echo  Descargalo en: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Verificar dependencias e instalarlas si faltan
echo  Verificando dependencias...
python -c "import pandas" >nul 2>&1
if errorlevel 1 (
    echo  Instalando pandas...
    pip install pandas --quiet
)
python -c "import openpyxl" >nul 2>&1
if errorlevel 1 (
    echo  Instalando openpyxl...
    pip install openpyxl --quiet
)

echo  Dependencias OK.
echo.

REM Ejecutar el script de inicialización
python init_db.py

if errorlevel 1 (
    echo.
    echo  [ERROR] Ocurrio un problema al inicializar la base de datos.
    pause
    exit /b 1
)

exit /b 0
