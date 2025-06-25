#!/usr/bin/env python3
"""
Sistema de Automação Completo - Império Rapidinhas
Executa capturas automáticas e mantém dashboard atualizado continuamente
"""
import os
import sys
import json
import time
import logging
import schedule
import threading
import webbrowser
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver

class ImperioAutomationSystem:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.config_file = self.base_dir / 'config' / 'config.json'
        self.data_dir = self.base_dir / 'data' / 'captures'
        self.logs_dir = self.base_dir / 'logs'
        self.dashboard_file = self.base_dir / 'dashboard_gerencial.html'
        
        # Cria diretórios necessários
        for directory in [self.data_dir, self.logs_dir, self.config_file.parent]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Configurar logging
        self.setup_logging()
        
        # Estado do sistema
        self.is_running = False
        self.capture_thread = None
        self.server_thread = None
        self.last_capture_time = None
        self.capture_count = 0
        self.api_server = None
        
    def setup_logging(self):
        """Configura sistema de logging"""
        log_file = self.logs_dir / f'automation_{datetime.now().strftime("%Y%m%d")}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self):
        """Carrega configurações"""
        if not self.config_file.exists():
            self.create_default_config()
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_config(self, config):
        """Salva configurações"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    
    def create_default_config(self):
        """Cria configuração padrão"""
        self.logger.info("Criando configuração padrão...")
        
        config = {
            'imperio': {
                'username': input("Digite seu usuário do Império Rapidinhas: "),
                'password': input("Digite sua senha: "),
                'base_url': 'https://dashboard.imperiorapidinhas.me'
            },
            'automation': {
                'enabled': True,
                'capture_times': ['06:00', '10:00', '14:00', '18:00', '22:00'],
                'capture_interval_minutes': 0,  # 0 = usar apenas horários fixos
                'use_headless': True,
                'capture_on_startup': True,
                'retry_on_failure': True,
                'max_retries': 3,
                'dashboard_port': 8080,
                'api_port': 8081
            },
            'data_management': {
                'keep_days': 365,  # Manter dados por 1 ano
                'compress_old_data': True,
                'backup_enabled': True,
                'backup_days': [1, 15]  # Dias do mês para backup
            },
            'notifications': {
                'enabled': False,
                'email': '',
                'webhook_url': '',
                'notify_on_error': True,
                'notify_on_success': False
            }
        }
        
        self.save_config(config)
        self.logger.info("Configuração criada com sucesso!")
    
    def run_capture(self, headless=None):
        """Executa captura de dados"""
        config = self.load_config()
        
        if headless is None:
            headless = config['automation']['use_headless']
        
        self.logger.info(f"Iniciando captura (headless={headless})...")
        
        try:
            # Importa e executa captura
            from capture_unlimited import ImperioRapidinhaSCaptureUnlimited
            
            capture = ImperioRapidinhaSCaptureUnlimited(str(self.config_file))
            result = capture.run(headless=headless, capture_details=False)
            
            if result:
                self.capture_count += 1
                self.last_capture_time = datetime.now()
                self.logger.info(f"✅ Captura #{self.capture_count} concluída: {result}")
                
                # Atualiza manifest
                self.update_manifest()
                
                # Notifica se configurado
                if config['notifications']['enabled'] and config['notifications']['notify_on_success']:
                    self.send_notification("Captura concluída com sucesso!", "success")
                
                return True
            else:
                raise Exception("Captura retornou resultado vazio")
                
        except Exception as e:
            self.logger.error(f"❌ Erro na captura: {e}")
            
            # Retry se configurado
            if config['automation']['retry_on_failure']:
                max_retries = config['automation']['max_retries']
                for attempt in range(1, max_retries):
                    self.logger.info(f"Tentativa {attempt + 1} de {max_retries}...")
                    time.sleep(30)  # Aguarda 30 segundos
                    
                    try:
                        return self.run_capture(headless)
                    except:
                        continue
            
            # Notifica erro
            if config['notifications']['enabled'] and config['notifications']['notify_on_error']:
                self.send_notification(f"Erro na captura: {str(e)}", "error")
            
            return False
    
    def update_manifest(self):
        """Atualiza arquivo manifest com lista de capturas"""
        manifest_file = self.data_dir / 'manifest.json'
        
        # Lista todos os arquivos de captura
        capture_files = sorted(self.data_dir.glob('captura_*.json'), reverse=True)
        
        manifest = {
            'updated': datetime.now().isoformat(),
            'total_files': len(capture_files),
            'files': []
        }
        
        for file in capture_files[:100]:  # Limita a 100 mais recentes no manifest
            try:
                # Lê resumo do arquivo
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                manifest['files'].append({
                    'filename': file.name,
                    'path': str(file.relative_to(self.base_dir)),
                    'timestamp': data['captura']['timestamp'],
                    'timestamp_unix': data['captura'].get('timestamp_unix', 0),
                    'total_rifas': data['resumo_geral']['total_rifas'],
                    'arrecadado_total': data['resumo_geral']['arrecadado_total'],
                    'size_kb': file.stat().st_size / 1024
                })
            except Exception as e:
                self.logger.warning(f"Erro ao ler {file}: {e}")
        
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        
        self.logger.info("Manifest atualizado")
    
    def schedule_captures(self):
        """Agenda capturas automáticas"""
        config = self.load_config()
        
        if not config['automation']['enabled']:
            self.logger.info("Automação desabilitada")
            return
        
        # Limpa agendamentos anteriores
        schedule.clear()
        
        # Agenda por horários fixos
        capture_times = config['automation']['capture_times']
        for time_str in capture_times:
            schedule.every().day.at(time_str).do(self.run_capture)
            self.logger.info(f"Captura agendada para: {time_str}")
        
        # Ou agenda por intervalo
        interval = config['automation']['capture_interval_minutes']
        if interval > 0:
            schedule.every(interval).minutes.do(self.run_capture)
            self.logger.info(f"Captura agendada a cada {interval} minutos")
        
        # Agenda limpeza diária
        schedule.every().day.at("03:00").do(self.cleanup_old_data)
        
        # Agenda backup
        if config['data_management']['backup_enabled']:
            schedule.every().day.at("04:00").do(self.check_backup)
    
    def run_scheduler(self):
        """Executa o agendador em loop"""
        self.is_running = True
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(30)  # Verifica a cada 30 segundos
            except Exception as e:
                self.logger.error(f"Erro no scheduler: {e}")
                time.sleep(60)
    
    def start_api_server(self):
        """Inicia servidor API para o dashboard"""
        config = self.load_config()
        port = config['automation']['api_port']
        
        class APIHandler(BaseHTTPRequestHandler):
            automation_system = self
            
            def log_message(self, format, *args):
                # Suprime logs do servidor HTTP
                pass
            
            def do_GET(self):
                if self.path == '/api/latest-data':
                    self.handle_latest_data()
                elif self.path == '/api/manifest':
                    self.handle_manifest()
                elif self.path == '/api/status':
                    self.handle_status()
                elif self.path.startswith('/api/data/'):
                    self.handle_data_file()
                else:
                    self.send_error(404)
            
            def do_POST(self):
                if self.path == '/api/capture/start':
                    self.handle_start_capture()
                else:
                    self.send_error(404)
            
            def handle_latest_data(self):
                """Retorna dados mais recentes"""
                try:
                    capture_files = sorted(
                        self.automation_system.data_dir.glob('captura_*.json'), 
                        reverse=True
                    )
                    
                    if capture_files:
                        with open(capture_files[0], 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        self.send_json_response(data)
                    else:
                        self.send_json_response({'error': 'Nenhum dado disponível'}, 404)
                        
                except Exception as e:
                    self.send_json_response({'error': str(e)}, 500)
            
            def handle_manifest(self):
                """Retorna manifest"""
                manifest_file = self.automation_system.data_dir / 'manifest.json'
                
                if manifest_file.exists():
                    with open(manifest_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    self.send_json_response(data)
                else:
                    self.send_json_response({'files': []})
            
            def handle_status(self):
                """Retorna status do sistema"""
                config = self.automation_system.load_config()
                
                status = {
                    'running': self.automation_system.is_running,
                    'last_capture': self.automation_system.last_capture_time.isoformat() 
                        if self.automation_system.last_capture_time else None,
                    'capture_count': self.automation_system.capture_count,
                    'automation_enabled': config['automation']['enabled'],
                    'next_capture': self.get_next_capture_time()
                }
                
                self.send_json_response(status)
            
            def handle_data_file(self):
                """Retorna arquivo de dados específico"""
                filename = self.path.split('/')[-1]
                filepath = self.automation_system.data_dir / filename
                
                if filepath.exists() and filepath.suffix == '.json':
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    self.send_json_response(data)
                else:
                    self.send_error(404)
            
            def handle_start_capture(self):
                """Inicia captura manual"""
                # Executa em thread separada
                thread = threading.Thread(
                    target=self.automation_system.run_capture,
                    args=(False,)  # Com interface
                )
                thread.start()
                
                self.send_json_response({
                    'status': 'Captura iniciada',
                    'message': 'A captura está sendo executada em background'
                })
            
            def get_next_capture_time(self):
                """Obtém próximo horário de captura"""
                jobs = schedule.get_jobs()
                if jobs:
                    next_run = min(job.next_run for job in jobs if job.next_run)
                    return next_run.isoformat() if next_run else None
                return None
            
            def send_json_response(self, data, status=200):
                """Envia resposta JSON"""
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())
        
        # Configura handler
        APIHandler.automation_system = self
        
        # Inicia servidor
        try:
            self.api_server = HTTPServer(('localhost', port), APIHandler)
            self.logger.info(f"API Server iniciado em http://localhost:{port}")
            
            server_thread = threading.Thread(target=self.api_server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar API server: {e}")
    
    def start_dashboard_server(self):
        """Inicia servidor para o dashboard"""
        config = self.load_config()
        port = config['automation']['dashboard_port']
        
        # Cria dashboard se não existir
        if not self.dashboard_file.exists():
            self.create_dashboard()
        
        # Servidor simples de arquivos
        os.chdir(self.base_dir)
        
        Handler = socketserver.TCPServer.allow_reuse_address = True
        
        class DashboardHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass
            
            def do_GET(self):
                if self.path == '/' or self.path == '/dashboard':
                    self.path = '/dashboard_gerencial.html'
                
                try:
                    file_path = self.path[1:]  # Remove /
                    
                    if Path(file_path).exists():
                        self.send_response(200)
                        
                        # Determina content-type
                        if file_path.endswith('.html'):
                            self.send_header('Content-Type', 'text/html')
                        elif file_path.endswith('.json'):
                            self.send_header('Content-Type', 'application/json')
                        else:
                            self.send_header('Content-Type', 'text/plain')
                        
                        self.end_headers()
                        
                        with open(file_path, 'rb') as f:
                            self.wfile.write(f.read())
                    else:
                        self.send_error(404)
                        
                except Exception as e:
                    self.send_error(500)
        
        try:
            httpd = socketserver.TCPServer(("", port), DashboardHandler)
            self.logger.info(f"Dashboard disponível em http://localhost:{port}")
            
            # Abre no navegador
            webbrowser.open(f'http://localhost:{port}')
            
            # Inicia em thread
            server_thread = threading.Thread(target=httpd.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            self.server_thread = server_thread
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar dashboard server: {e}")
    
    def create_dashboard(self):
        """Cria arquivo do dashboard"""
        self.logger.info("Criando dashboard...")
        
        # Copia conteúdo do artifact dashboard-gerencial
        # Em produção, isso viria de um template ou seria gerado
        
        dashboard_content = """
        <!-- Conteúdo do dashboard seria inserido aqui -->
        <!-- Use o conteúdo do artifact 'dashboard-gerencial' -->
        """
        
        with open(self.dashboard_file, 'w', encoding='utf-8') as f:
            f.write(dashboard_content)
        
        self.logger.info("Dashboard criado")
    
    def cleanup_old_data(self):
        """Limpa dados antigos"""
        config = self.load_config()
        keep_days = config['data_management']['keep_days']
        
        self.logger.info(f"Limpando arquivos com mais de {keep_days} dias...")
        
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        removed_count = 0
        
        for file in self.data_dir.glob('captura_*.json'):
            try:
                # Verifica data do arquivo
                file_date = datetime.fromtimestamp(file.stat().st_mtime)
                
                if file_date < cutoff_date:
                    if config['data_management']['compress_old_data']:
                        # Comprime antes de remover
                        self.compress_file(file)
                    else:
                        file.unlink()
                    
                    removed_count += 1
                    
            except Exception as e:
                self.logger.error(f"Erro ao processar {file}: {e}")
        
        if removed_count > 0:
            self.logger.info(f"Removidos {removed_count} arquivos antigos")
            self.update_manifest()
    
    def compress_file(self, file_path):
        """Comprime arquivo antes de arquivar"""
        import gzip
        import shutil
        
        archive_dir = self.data_dir / 'archive'
        archive_dir.mkdir(exist_ok=True)
        
        compressed_file = archive_dir / f"{file_path.name}.gz"
        
        with open(file_path, 'rb') as f_in:
            with gzip.open(compressed_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        file_path.unlink()
        self.logger.info(f"Arquivo comprimido: {compressed_file.name}")
    
    def check_backup(self):
        """Verifica e executa backup se necessário"""
        config = self.load_config()
        today = datetime.now().day
        
        if today in config['data_management']['backup_days']:
            self.create_backup()
    
    def create_backup(self):
        """Cria backup dos dados"""
        import zipfile
        
        backup_dir = self.base_dir / 'backups'
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_dir / f'backup_{timestamp}.zip'
        
        self.logger.info(f"Criando backup: {backup_file}")
        
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Adiciona arquivos de dados
            for file in self.data_dir.rglob('*.json'):
                zipf.write(file, file.relative_to(self.base_dir))
            
            # Adiciona configuração
            if self.config_file.exists():
                zipf.write(self.config_file, self.config_file.relative_to(self.base_dir))
        
        self.logger.info(f"Backup criado: {backup_file} ({backup_file.stat().st_size / 1024 / 1024:.2f} MB)")
    
    def send_notification(self, message, level="info"):
        """Envia notificação (placeholder)"""
        # Implementar envio real de notificações
        self.logger.info(f"[NOTIFICAÇÃO] {level.upper()}: {message}")
    
    def get_system_stats(self):
        """Obtém estatísticas do sistema"""
        stats = {
            'uptime': None,
            'total_captures': self.capture_count,
            'last_capture': self.last_capture_time,
            'data_size_mb': 0,
            'total_rifas': 0,
            'total_revenue': 0
        }
        
        # Calcula tamanho dos dados
        for file in self.data_dir.glob('*.json'):
            stats['data_size_mb'] += file.stat().st_size / 1024 / 1024
        
        # Lê estatísticas do manifest
        manifest_file = self.data_dir / 'manifest.json'
        if manifest_file.exists():
            with open(manifest_file, 'r') as f:
                manifest = json.load(f)
                if manifest['files']:
                    latest = manifest['files'][0]
                    stats['total_rifas'] = latest['total_rifas']
                    stats['total_revenue'] = latest['arrecadado_total']
        
        return stats
    
    def run(self):
        """Executa o sistema completo"""
        print("\n" + "="*60)
        print("🎰 SISTEMA AUTOMATIZADO - IMPÉRIO RAPIDINHAS")
        print("="*60)
        
        # Carrega configuração
        config = self.load_config()
        
        # Inicia servidores
        self.start_api_server()
        self.start_dashboard_server()
        
        # Captura inicial se configurado
        if config['automation']['capture_on_startup']:
            self.logger.info("Executando captura inicial...")
            self.run_capture()
        
        # Agenda capturas
        self.schedule_captures()
        
        # Inicia scheduler em thread
        self.capture_thread = threading.Thread(target=self.run_scheduler)
        self.capture_thread.daemon = True
        self.capture_thread.start()
        
        self.logger.info("✅ Sistema iniciado e rodando!")
        self.logger.info("📊 Dashboard: http://localhost:{}".format(
            config['automation']['dashboard_port']
        ))
        
        # Menu interativo
        while True:
            try:
                print("\n" + "-"*40)
                print("COMANDOS DISPONÍVEIS:")
                print("  c - Executar captura manual")
                print("  s - Ver status do sistema")
                print("  r - Recarregar configurações")
                print("  b - Criar backup")
                print("  q - Sair")
                print("-"*40)
                
                cmd = input("\nComando: ").strip().lower()
                
                if cmd == 'c':
                    print("Iniciando captura manual...")
                    self.run_capture(headless=False)
                    
                elif cmd == 's':
                    stats = self.get_system_stats()
                    print("\nSTATUS DO SISTEMA:")
                    print(f"  Capturas realizadas: {stats['total_captures']}")
                    print(f"  Última captura: {stats['last_capture']}")
                    print(f"  Tamanho dos dados: {stats['data_size_mb']:.2f} MB")
                    print(f"  Total de rifas: {stats['total_rifas']}")
                    print(f"  Arrecadação total: R$ {stats['total_revenue']:,.2f}")
                    
                elif cmd == 'r':
                    print("Recarregando configurações...")
                    self.schedule_captures()
                    print("✅ Configurações recarregadas!")
                    
                elif cmd == 'b':
                    print("Criando backup...")
                    self.create_backup()
                    
                elif cmd == 'q':
                    print("\nParando sistema...")
                    self.is_running = False
                    if self.api_server:
                        self.api_server.shutdown()
                    break
                    
                else:
                    print("Comando inválido!")
                    
            except KeyboardInterrupt:
                print("\n\nInterrompido pelo usuário")
                self.is_running = False
                break
            except Exception as e:
                self.logger.error(f"Erro no menu: {e}")
        
        self.logger.info("Sistema finalizado")

def main():
    """Função principal"""
    # Verifica argumentos
    if len(sys.argv) > 1:
        if sys.argv[1] == '--daemon':
            # Modo daemon (sem interação)
            print("Iniciando em modo daemon...")
            automation = ImperioAutomationSystem()
            
            # Remove menu interativo
            automation.start_api_server()
            automation.start_dashboard_server()
            
            config = automation.load_config()
            if config['automation']['capture_on_startup']:
                automation.run_capture()
            
            automation.schedule_captures()
            automation.run_scheduler()  # Bloqueia aqui
            
        elif sys.argv[1] == '--help':
            print("Uso:")
            print("  python automation_system.py         # Modo interativo")
            print("  python automation_system.py --daemon # Modo daemon")
            sys.exit(0)
    else:
        # Modo interativo padrão
        automation = ImperioAutomationSystem()
        automation.run()

if __name__ == "__main__":
    main()