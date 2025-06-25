@echo off
REM ===================================================
REM INICIAR_DASHBOARD.bat - Inicia o sistema completo
REM ===================================================

title Imperio Rapidinhas - Dashboard Gerencial
color 0A

echo.
echo  ================================================
echo      IMPERIO RAPIDINHAS - DASHBOARD GERENCIAL
echo  ================================================
echo.

REM Verifica se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERRO] Python nao encontrado!
    echo.
    echo  Por favor instale Python 3.8 ou superior:
    echo  https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo  [OK] Python encontrado
echo.

REM Inicia o sistema
echo  Iniciando sistema...
echo.

python quick_start.py --start

pause