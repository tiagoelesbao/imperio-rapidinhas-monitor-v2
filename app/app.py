from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from functools import wraps

def create_app():
    # Configuração correta dos caminhos
    BASE_DIR = Path(__file__).parent.parent  # Volta para a raiz do projeto
    TEMPLATE_DIR = BASE_DIR / 'templates'    # Templates estão na raiz
    
    app = Flask(__name__, 
                template_folder=str(TEMPLATE_DIR),  # Define onde estão os templates
                static_folder=str(BASE_DIR / 'static'))  # Define onde estão os arquivos estáticos
    
    app.config['SECRET_KEY'] = 'imperio-rapidinhas-2025'
    
    # Diretórios
    DATA_DIR = BASE_DIR / 'data' / 'captures'
    CONFIG_DIR = BASE_DIR / 'config'
    
    # Criar diretórios se não existirem
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'logged_in' not in session:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    
    @app.route('/')
    def index():
        return redirect(url_for('dashboard'))
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            if username == 'admin' and password == 'admin123':
                session['logged_in'] = True
                session['username'] = username
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error='Usuário ou senha inválidos')
        
        return render_template('login.html')
    
    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard/index.html')
    
    @app.route('/api/latest-data')
    @login_required
    def api_latest_data():
        """Retorna os dados mais recentes"""
        try:
            # Procura arquivos de captura
            capture_files = []
            
            # Procura em data/captures
            if DATA_DIR.exists():
                capture_files.extend(DATA_DIR.glob('captura_*.json'))
            
            # Procura em data/
            data_parent = BASE_DIR / 'data'
            if data_parent.exists():
                capture_files.extend(data_parent.glob('captura_*.json'))
            
            # Procura na raiz (onde estão seus arquivos de exemplo)
            capture_files.extend(BASE_DIR.glob('captura_*.json'))
            capture_files.extend(BASE_DIR.glob('resumo_*.json'))
            
            if not capture_files:
                return jsonify({'error': 'Nenhum dado disponível'}), 404
            
            # Pega o arquivo mais recente
            latest_file = max(capture_files, key=lambda p: p.stat().st_mtime)
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return jsonify(data)
            
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/capture', methods=['POST'])
    @login_required
    def api_capture():
        """Inicia captura de dados"""
        try:
            # Procura script de captura
            capture_scripts = [
                'capture_corrected.py',
                'capture_complete.py',
                'captura.py'
            ]
            
            capture_script = None
            for script in capture_scripts:
                script_path = BASE_DIR / script
                if script_path.exists():
                    capture_script = str(script_path)
                    break
            
            if not capture_script:
                return jsonify({
                    'error': 'Sistema de captura não encontrado',
                    'detail': 'Nenhum script de captura disponível'
                }), 404
            
            # Executa captura em processo separado
            if os.name == 'nt':  # Windows
                # Cria um arquivo .bat temporário
                bat_file = BASE_DIR / 'temp_capture.bat'
                with open(bat_file, 'w') as f:
                    f.write(f'@echo off\n')
                    f.write(f'cd /d "{BASE_DIR}"\n')
                    f.write(f'python "{capture_script}"\n')
                    f.write(f'pause\n')
                
                subprocess.Popen(['cmd', '/c', 'start', 'Captura Imperio Rapidinhas', str(bat_file)])
            else:
                # Linux/Mac
                subprocess.Popen([sys.executable, capture_script])
            
            return jsonify({
                'status': 'success',
                'message': 'Captura iniciada! Aguarde alguns minutos e recarregue a página.'
            })
            
        except Exception as e:
            return jsonify({
                'error': 'Erro ao iniciar captura',
                'detail': str(e)
            }), 500
    
    @app.route('/api/status')
    @login_required
    def api_status():
        """Retorna status do sistema"""
        try:
            # Conta arquivos de dados
            capture_files = list(DATA_DIR.glob('captura_*.json')) if DATA_DIR.exists() else []
            capture_files.extend(BASE_DIR.glob('captura_*.json'))
            
            # Verifica configuração
            config_file = CONFIG_DIR / 'config.json'
            config_exists = config_file.exists()
            
            status = {
                'data_files': len(set(capture_files)),  # Remove duplicatas
                'config_exists': config_exists,
                'last_update': None
            }
            
            if capture_files:
                latest = max(capture_files, key=lambda p: p.stat().st_mtime)
                status['last_update'] = datetime.fromtimestamp(
                    latest.stat().st_mtime
                ).strftime('%d/%m/%Y %H:%M:%S')
            
            return jsonify(status)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return app, None

# Se executado diretamente
if __name__ == '__main__':
    app, _ = create_app()
    
    print("\n" + "="*60)
    print("🎰 IMPÉRIO RAPIDINHAS - SERVIDOR WEB")
    print("="*60)
    print("\n🌐 Servidor iniciando...")
    print("📍 Acesse: http://localhost:5001")
    print("🔑 Login: admin / admin123")
    print("\n💡 Pressione Ctrl+C para parar")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5001, debug=True)