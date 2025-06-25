#!/usr/bin/env python3
"""
Script de Inicialização Rápida - Império Rapidinhas
Inicia o sistema completo com um comando
"""
import os
import sys
import time
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime

class QuickStart:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.python_cmd = sys.executable
        
    def check_requirements(self):
        """Verifica e instala requisitos"""
        print("🔍 Verificando requisitos...")
        
        required_packages = [
            'selenium',
            'webdriver-manager',
            'beautifulsoup4',
            'requests',
            'schedule',
            'pandas',
            'openpyxl'
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing.append(package)
        
        if missing:
            print(f"📦 Instalando pacotes: {', '.join(missing)}")
            subprocess.check_call([
                self.python_cmd, '-m', 'pip', 'install'] + missing
            )
        
        print("✅ Requisitos OK!")
    
    def setup_directories(self):
        """Cria estrutura de diretórios"""
        dirs = [
            'config',
            'data/captures',
            'data/archive',
            'logs',
            'backups'
        ]
        
        for dir_path in dirs:
            (self.base_dir / dir_path).mkdir(parents=True, exist_ok=True)
        
        print("📁 Diretórios criados!")
    
    def check_config(self):
        """Verifica se existe configuração"""
        config_file = self.base_dir / 'config' / 'config.json'
        
        if not config_file.exists():
            print("\n⚠️  CONFIGURAÇÃO INICIAL NECESSÁRIA!")
            print("="*50)
            return False
        
        return True
    
    def create_dashboard(self):
        """Cria arquivo do dashboard se não existir"""
        dashboard_file = self.base_dir / 'dashboard_gerencial.html'
        
        if not dashboard_file.exists():
            print("📄 Criando dashboard...")
            # Aqui você deve copiar o conteúdo do artifact 'dashboard-gerencial'
            # Por simplicidade, vamos criar um placeholder
            with open(dashboard_file, 'w', encoding='utf-8') as f:
                f.write("<!-- Dashboard será criado aqui -->")
            print("✅ Dashboard criado!")
    
    def start_system(self, mode='interactive'):
        """Inicia o sistema"""
        print(f"\n🚀 Iniciando sistema em modo {mode}...")
        
        automation_script = self.base_dir / 'automation_system.py'
        
        if not automation_script.exists():
            print("❌ Script de automação não encontrado!")
            print("   Certifique-se de ter o arquivo 'automation_system.py'")
            return False
        
        if mode == 'daemon':
            # Modo daemon - roda em background
            if os.name == 'nt':  # Windows
                subprocess.Popen(
                    [self.python_cmd, str(automation_script), '--daemon'],
                    creationflags=subprocess.CREATE_NEW_WINDOW
                )
            else:  # Linux/Mac
                subprocess.Popen(
                    [self.python_cmd, str(automation_script), '--daemon'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            print("✅ Sistema iniciado em background!")
            time.sleep(3)
            
            # Abre dashboard
            webbrowser.open('http://localhost:8080')
            
            print("\n📊 Dashboard aberto no navegador!")
            print("   URL: http://localhost:8080")
            print("\n💡 O sistema está rodando em background.")
            print("   Para parar, use o Gerenciador de Tarefas ou 'pkill python'")
            
        else:
            # Modo interativo
            subprocess.call([self.python_cmd, str(automation_script)])
        
        return True
    
    def show_menu(self):
        """Menu principal"""
        while True:
            print("\n" + "="*60)
            print("🎰 IMPÉRIO RAPIDINHAS - INICIALIZAÇÃO RÁPIDA")
            print("="*60)
            print("\n1. 🚀 Iniciar Sistema Completo (Recomendado)")
            print("2. 🤖 Iniciar em Modo Daemon (Background)")
            print("3. 📊 Apenas Abrir Dashboard")
            print("4. 🔧 Verificar Instalação")
            print("5. 📦 Criar Backup")
            print("6. ❌ Sair")
            
            choice = input("\nEscolha uma opção (1-6): ").strip()
            
            if choice == '1':
                self.check_requirements()
                self.setup_directories()
                self.create_dashboard()
                
                if self.check_config():
                    self.start_system('interactive')
                else:
                    print("\nExecute primeiro o sistema para configurar credenciais.")
                    
            elif choice == '2':
                self.check_requirements()
                self.setup_directories()
                self.create_dashboard()
                
                if self.check_config():
                    self.start_system('daemon')
                    input("\nPressione ENTER para voltar ao menu...")
                else:
                    print("\nExecute primeiro o sistema para configurar credenciais.")
                    
            elif choice == '3':
                webbrowser.open('http://localhost:8080')
                print("📊 Dashboard aberto no navegador!")
                
            elif choice == '4':
                print("\n🔍 Verificando instalação...")
                self.check_requirements()
                self.setup_directories()
                
                if self.check_config():
                    print("✅ Sistema configurado e pronto!")
                else:
                    print("⚠️  Sistema precisa ser configurado!")
                
                input("\nPressione ENTER para continuar...")
                
            elif choice == '5':
                self.create_backup()
                
            elif choice == '6':
                print("\n👋 Até logo!")
                break
            else:
                print("\n❌ Opção inválida!")
    
    def create_backup(self):
        """Cria backup manual"""
        import zipfile
        import json
        
        backup_dir = self.base_dir / 'backups'
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_dir / f'backup_manual_{timestamp}.zip'
        
        print(f"\n📦 Criando backup: {backup_file.name}")
        
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Backup de dados
            data_dir = self.base_dir / 'data'
            if data_dir.exists():
                for file in data_dir.rglob('*.json'):
                    zipf.write(file, file.relative_to(self.base_dir))
            
            # Backup de config
            config_file = self.base_dir / 'config' / 'config.json'
            if config_file.exists():
                zipf.write(config_file, config_file.relative_to(self.base_dir))
            
            # Backup de logs
            logs_dir = self.base_dir / 'logs'
            if logs_dir.exists():
                for file in logs_dir.glob('*.log'):
                    zipf.write(file, file.relative_to(self.base_dir))
        
        size_mb = backup_file.stat().st_size / 1024 / 1024
        print(f"✅ Backup criado com sucesso! ({size_mb:.2f} MB)")

def main():
    """Função principal"""
    quick_start = QuickStart()
    
    # Se passou argumento direto
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg in ['--start', '-s']:
            quick_start.check_requirements()
            quick_start.setup_directories()
            quick_start.create_dashboard()
            
            if quick_start.check_config():
                quick_start.start_system('interactive')
            else:
                print("\nConfigure o sistema primeiro!")
                
        elif arg in ['--daemon', '-d']:
            quick_start.check_requirements()
            quick_start.setup_directories()
            quick_start.create_dashboard()
            
            if quick_start.check_config():
                quick_start.start_system('daemon')
            else:
                print("\nConfigure o sistema primeiro!")
                
        elif arg in ['--help', '-h']:
            print("Uso:")
            print("  python quick_start.py          # Menu interativo")
            print("  python quick_start.py --start  # Iniciar sistema")
            print("  python quick_start.py --daemon # Iniciar em background")
            print("  python quick_start.py --help   # Mostrar ajuda")
        else:
            print(f"Argumento inválido: {arg}")
            print("Use --help para ver opções disponíveis")
    else:
        # Menu interativo
        quick_start.show_menu()

if __name__ == "__main__":
    main()