#!/usr/bin/env python3
"""
Imperio Rapidinhas - Sistema de Gestão
Ponto de entrada único do sistema
"""
import os
import sys
import click
import logging
from pathlib import Path
from datetime import datetime

# Adiciona o diretório ao path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(ROOT_DIR / 'logs' / f'system_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@click.group()
def cli():
    """Imperio Rapidinhas - Sistema de Gestão"""
    pass

@cli.command()
@click.option('--host', default='0.0.0.0', help='Host do servidor')
@click.option('--port', default=5000, type=int, help='Porta do servidor')
@click.option('--debug', is_flag=True, help='Modo debug')
def server(host, port, debug):
    """Inicia o servidor web"""
    logger.info(f"Iniciando servidor em {host}:{port}")
    
    # Verifica porta
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    
    if result == 0:
        logger.warning(f"Porta {port} em uso!")
        # Busca porta livre
        for p in range(port + 1, port + 100):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if sock.connect_ex(('127.0.0.1', p)) != 0:
                port = p
                logger.info(f"Usando porta alternativa: {port}")
                sock.close()
                break
            sock.close()
    
    # Importa e inicia aplicação
    try:
        from app.app import create_app
        app, socketio = create_app()
        
        logger.info("="*60)
        logger.info("IMPÉRIO RAPIDINHAS - SERVIDOR WEB")
        logger.info("="*60)
        logger.info(f"URL Local: http://localhost:{port}")
        logger.info(f"URL Rede: http://{host}:{port}")
        logger.info("Login padrão: admin / admin123")
        logger.info("="*60)
        
        # Abre navegador
        import webbrowser
        webbrowser.open(f'http://localhost:{port}')
        
        # Inicia servidor
        if debug:
            socketio.run(app, host=host, port=port, debug=True)
        else:
            # Produção - usa eventlet ou waitress
            try:
                import eventlet
                eventlet.monkey_patch()
                socketio.run(app, host=host, port=port, debug=False)
            except ImportError:
                logger.warning("Eventlet não encontrado, usando Waitress...")
                from waitress import serve
                serve(app, host=host, port=port, threads=4)
                
    except Exception as e:
        logger.error(f"Erro ao iniciar servidor: {e}")
        import traceback
        traceback.print_exc()

@cli.command()
@click.option('--headless', is_flag=True, help='Executa sem interface')
@click.option('--quick', is_flag=True, help='Captura rápida sem relatórios')
def capture(headless, quick):
    """Executa captura de dados"""
    logger.info("Iniciando captura de dados...")
    
    try:
        from app.services.capture import CaptureService
        service = CaptureService()
        
        if quick:
            service.quick_capture(headless=headless)
        else:
            service.full_capture(headless=headless)
            
        logger.info("Captura concluída!")
        
    except Exception as e:
        logger.error(f"Erro na captura: {e}")
        import traceback
        traceback.print_exc()

@cli.command()
def install():
    """Instala e configura o sistema"""
    logger.info("Iniciando instalação...")
    
    try:
        from scripts.install import Installer
        installer = Installer()
        installer.run()
        
    except Exception as e:
        logger.error(f"Erro na instalação: {e}")

@cli.command()
@click.option('--days', default=7, help='Manter arquivos dos últimos N dias')
def clean(days):
    """Limpa arquivos antigos"""
    logger.info(f"Limpando arquivos com mais de {days} dias...")
    
    try:
        from scripts.clean import Cleaner
        cleaner = Cleaner()
        cleaner.clean_old_files(days)
        
    except Exception as e:
        logger.error(f"Erro na limpeza: {e}")

@cli.command()
def backup():
    """Realiza backup dos dados"""
    logger.info("Iniciando backup...")
    
    try:
        from scripts.backup import BackupManager
        backup_mgr = BackupManager()
        backup_mgr.create_backup()
        
    except Exception as e:
        logger.error(f"Erro no backup: {e}")

@cli.command()
def status():
    """Mostra status do sistema"""
    from rich.console import Console
    from rich.table import Table
    from rich import box
    import json
    
    console = Console()
    
    # Cabeçalho
    console.print("\n[bold cyan]IMPÉRIO RAPIDINHAS - STATUS DO SISTEMA[/bold cyan]")
    console.print("=" * 60)
    
    # Verifica configuração
    config_file = ROOT_DIR / 'config' / 'config.json'
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
        console.print("✅ Configuração: [green]OK[/green]")
        console.print(f"   Usuário: {config['imperio']['username']}")
    else:
        console.print("❌ Configuração: [red]Não encontrada[/red]")
    
    # Verifica dados
    data_dir = ROOT_DIR / 'data' / 'captures'
    if data_dir.exists():
        captures = list(data_dir.glob('*.json'))
        console.print(f"\n📊 Capturas: [cyan]{len(captures)}[/cyan] arquivos")
        
        if captures:
            latest = max(captures, key=lambda p: p.stat().st_mtime)
            console.print(f"   Última: {latest.name}")
    
    # Tabela de estatísticas
    if captures:
        table = Table(title="\nEstatísticas Recentes", box=box.ROUNDED)
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", style="green")
        
        # Carrega última captura
        with open(latest, 'r') as f:
            data = json.load(f)
            summary = data.get('resumo_geral', {})
            
        table.add_row("Total de Rifas", str(summary.get('total_rifas', 0)))
        table.add_row("Arrecadação Total", f"R$ {summary.get('arrecadado_total', 0):,.2f}")
        table.add_row("Títulos Vendidos", f"{summary.get('titulos_total', 0):,}")
        table.add_row("Ticket Médio", f"R$ {summary.get('ticket_medio_geral', 0):.2f}")
        
        console.print(table)

@cli.command()
def shell():
    """Abre shell interativo"""
    import IPython
    from app.app import create_app
    
    app, socketio = create_app()
    
    with app.app_context():
        IPython.embed(
            banner1="Imperio Rapidinhas - Shell Interativo\n"
                   "Variáveis disponíveis: app, socketio\n"
        )

if __name__ == '__main__':
    # Cria diretórios necessários
    dirs = ['logs', 'data/captures', 'data/reports', 'data/analytics', 'config']
    for d in dirs:
        (ROOT_DIR / d).mkdir(parents=True, exist_ok=True)
    
    # Executa CLI
    cli()