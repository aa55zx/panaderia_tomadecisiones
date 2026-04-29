@echo off
title Panaderia El Ranchero - Inicializar Base de Datos

echo.
echo  =====================================================
echo    Panaderia El Ranchero - Inicializar Base de Datos
echo  =====================================================
echo.

cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python no esta instalado o no esta en el PATH.
    echo  Descargalo en: https://www.python.org/downloads/
    pause
    exit /b 1
)

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

python -c "import pymongo" >nul 2>&1
if errorlevel 1 (
    echo  Instalando pymongo...
    pip install pymongo --quiet
)

echo  Dependencias OK.
echo.

echo  Verificando MongoDB...
python -c "from pymongo import MongoClient; MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=2000).admin.command('ping')" >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [ERROR] No se puede conectar a MongoDB en localhost:27017
    echo.
    echo  Asegurate de que:
    echo    1. MongoDB Community esta instalado
    echo    2. El servicio "MongoDB" esta corriendo
    echo       ^(Busca "Servicios" en Windows y activa MongoDB^)
    echo.
    echo  Descarga MongoDB en:
    echo    https://www.mongodb.com/try/download/community
    echo.
    pause
    exit /b 1
)
echo  MongoDB: OK
echo.

python init_db.py

if errorlevel 1 (
    echo.
    echo  [ERROR] Ocurrio un problema al inicializar la base de datos.
    pause
    exit /b 1
)

exit /b 0
