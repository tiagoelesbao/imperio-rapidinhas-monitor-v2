@echo off
REM Gerenciador de Configuracao - Imperio Rapidinhas
title Gerenciador de Configuracao - Imperio Rapidinhas
color 0A

:menu
cls
echo ================================================
echo   GERENCIADOR DE CONFIGURACAO - IMPERIO RAPIDINHAS
echo ================================================
echo.
echo   1. Visualizar configuracao atual
echo   2. Corrigir configuracao (adicionar campos faltantes)
echo   3. Resetar configuracao (criar nova)
echo   4. Executar captura
echo   5. Sair
echo.
set /p choice="Escolha uma opcao (1-5): "

if "%choice%"=="1" goto view
if "%choice%"=="2" goto fix
if "%choice%"=="3" goto reset
if "%choice%"=="4" goto capture
if "%choice%"=="5" goto end

echo Opcao invalida!
pause
goto menu

:view
cls
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)
python view_config.py
pause
goto menu

:fix
cls
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)
python fix_config.py
pause
goto menu

:reset
cls
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)
python reset_config.py
pause
goto menu

:capture
cls
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)
python capture_unlimited.py
pause
goto menu

:end
exit