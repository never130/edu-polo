@echo off
chcp 65001 >nul
echo ========================================
echo   Sistema Educativo Polo
echo   Iniciando servidor Django...
echo ========================================
echo.

cd /d "%~dp0src"

echo Verificando Python...
python --version
echo.

echo Verificando configuración de Django...
python manage.py check
echo.

echo Iniciando servidor en http://127.0.0.1:8000
echo Presiona Ctrl+C para detener el servidor
echo.

python manage.py runserver 127.0.0.1:8000

pause



