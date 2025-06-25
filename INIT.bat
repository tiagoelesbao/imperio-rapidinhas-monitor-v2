@echo off
REM =========================================================
REM          IMPERIO RAPIDINHAS v2.0 - INICIALIZADOR
REM =========================================================
title Imperio Rapidinhas v2.0
color 0A

:menu
cls
echo.
echo  ===========================================================
echo      IMPERIO RAPIDINHAS - SISTEMA DE GESTAO v2.0
echo  ===========================================================
echo.
echo  Sistema Status:
python -c "import os; print('  [OK] Python instalado' if os.system('python --version >nul 2>&1')==0 else '  [X] Python NAO encontrado!')"
if exist venv\Scripts\activate.bat (
    echo   [OK] Ambiente virtual existe
) else (
    echo   [X] Ambiente virtual NAO existe
)
if exist config\config.json (
    echo   [OK] Sistema configurado
) else (
    echo   [!] Sistema NAO configurado
)
echo.
echo  ===========================================================
echo.
echo  1. INSTALACAO COMPLETA (primeira vez)
echo  2. Iniciar Servidor Web
echo  3. Executar Captura Manual
echo  4. Ver Status do Sistema
echo  5. Fazer Backup
echo  6. Migrar do Sistema Antigo
echo  7. Abrir Dashboard no Navegador
echo  8. Sair
echo.
set /p choice="  Escolha uma opcao (1-8): "

if "%choice%"=="1" goto install
if "%choice%"=="2" goto server
if "%choice%"=="3" goto capture
if "%choice%"=="4" goto status
if "%choice%"=="5" goto backup
if "%choice%"=="6" goto migrate
if "%choice%"=="7" goto browser
if "%choice%"=="8" goto end

echo.
echo  [!] Opcao invalida!
pause
goto menu

:install
cls
echo.
echo  ===========================================================
echo              INSTALACAO COMPLETA DO SISTEMA
echo  ===========================================================
echo.

REM Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERRO] Python nao encontrado!
    echo.
    echo  Por favor instale Python 3.8 ou superior:
    echo  https://www.python.org/downloads/
    echo.
    echo  IMPORTANTE: Marque "Add Python to PATH" durante instalacao!
    echo.
    pause
    goto menu
)

echo  [1/5] Criando ambiente virtual...
if not exist venv (
    python -m venv venv
    echo  [OK] Ambiente virtual criado
) else (
    echo  [OK] Ambiente virtual ja existe
)

echo.
echo  [2/5] Ativando ambiente...
call venv\Scripts\activate

echo.
echo  [3/5] Atualizando pip...
python -m pip install --upgrade pip --quiet

echo.
echo  [4/5] Instalando dependencias...
echo  (isso pode demorar alguns minutos)
pip install -r requirements.txt

echo.
echo  [5/5] Configurando sistema...
python run.py install

echo.
echo  ===========================================================
echo  [OK] INSTALACAO CONCLUIDA!
echo  ===========================================================
echo.
echo  Agora voce pode:
echo  - Opcao 2: Iniciar o servidor
echo  - Opcao 3: Executar captura
echo.
pause
goto menu

:server
cls
echo.
echo  ===========================================================
echo               INICIANDO SERVIDOR WEB
echo  ===========================================================
echo.

if not exist venv\Scripts\activate.bat (
    echo  [ERRO] Sistema nao instalado!
    echo         Execute a opcao 1 primeiro.
    pause
    goto menu
)

call venv\Scripts\activate
python run.py server

pause
goto menu

:capture
cls
echo.
echo  ===========================================================
echo              EXECUTANDO CAPTURA DE DADOS
echo  ===========================================================
echo.

if not exist venv\Scripts\activate.bat (
    echo  [ERRO] Sistema nao instalado!
    echo         Execute a opcao 1 primeiro.
    pause
    goto menu
)

echo  Escolha o tipo de captura:
echo.
echo  1. Captura completa (com interface)
echo  2. Captura headless (sem interface)
echo  3. Captura rapida (sem relatorios)
echo  4. Voltar
echo.
set /p cap_choice="  Escolha (1-4): "

call venv\Scripts\activate

if "%cap_choice%"=="1" python run.py capture
if "%cap_choice%"=="2" python run.py capture --headless
if "%cap_choice%"=="3" python run.py capture --quick
if "%cap_choice%"=="4" goto menu

pause
goto menu

:status
cls
call venv\Scripts\activate
python run.py status
echo.
pause
goto menu

:backup
cls
echo.
echo  ===========================================================
echo                   BACKUP DO SISTEMA
echo  ===========================================================
echo.
call venv\Scripts\activate
python run.py backup
echo.
pause
goto menu

:migrate
cls
echo.
echo  ===========================================================
echo            MIGRACAO DO SISTEMA ANTIGO
echo  ===========================================================
echo.
echo  ATENCAO: Este processo ira:
echo  - Fazer backup do sistema atual
echo  - Remover arquivos redundantes
echo  - Migrar dados e configuracoes
echo  - Criar nova estrutura
echo.
set /p confirm="  Tem certeza que deseja continuar? (S/N): "

if /i "%confirm%"=="S" (
    if exist migrate_to_v2.py (
        call venv\Scripts\activate
        python migrate_to_v2.py
    ) else (
        echo  [ERRO] Script de migracao nao encontrado!
    )
) else (
    echo  Operacao cancelada.
)

pause
goto menu

:browser
start http://localhost:5000
goto menu

:end
echo.
echo  Ate logo!
echo.
timeout /t 2 /nobreak >nul
exit