
# Imperio Rapidinhas - Start Server
Write-Host "=====================================" -ForegroundColor Green
Write-Host "IMPERIO RAPIDINHAS - SERVIDOR WEB" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""

# Ativa ambiente virtual
if (Test-Path "venv\Scripts\Activate.ps1") {
    & .\venv\Scripts\Activate.ps1
} else {
    Write-Host "ERRO: Ambiente virtual nao encontrado!" -ForegroundColor Red
    Write-Host "Execute: python -m venv venv" -ForegroundColor Yellow
    Read-Host "Pressione ENTER para sair"
    exit 1
}

# Inicia servidor
Write-Host "Iniciando servidor..." -ForegroundColor Cyan
python run_production_windows.py
