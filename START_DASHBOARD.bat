@echo off
title Imperio Rapidinhas - Dashboard
cls
echo.
echo ========================================
echo    IMPERIO RAPIDINHAS - DASHBOARD
echo ========================================
echo.

REM Verifica se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo Por favor instale Python 3.8 ou superior
    pause
    exit /b 1
)

REM Instala Flask se necessário
echo Verificando dependencias...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo Instalando Flask...
    pip install flask
)

echo.
echo Iniciando servidor...
echo.
echo Acesse: http://localhost:5001
echo Login: admin / admin123
echo.
echo Pressione Ctrl+C para parar
echo.

REM Inicia o servidor
cd /d "%~dp0"
python app/app.py

pause