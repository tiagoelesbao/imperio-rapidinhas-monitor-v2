
from flask import Flask, render_template_string, jsonify, request, redirect, url_for, send_from_directory
import json
import os
from pathlib import Path
from datetime import datetime

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'imperio-rapidinhas-key'
    
    # Templates HTML inline
    LOGIN_HTML = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - Imperio Rapidinhas</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
                color: white;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .login-container {
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                padding: 40px;
                width: 90%;
                max-width: 400px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
            }
            .logo {
                text-align: center;
                font-size: 3em;
                margin-bottom: 20px;
            }
            h2 {
                text-align: center;
                margin-bottom: 30px;
                font-weight: 300;
            }
            .form-group {
                margin-bottom: 20px;
            }
            input {
                width: 100%;
                padding: 15px;
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 10px;
                color: white;
                font-size: 16px;
                transition: all 0.3s;
            }
            input:focus {
                outline: none;
                border-color: #ff6b35;
                background: rgba(255, 255, 255, 0.15);
            }
            input::placeholder {
                color: rgba(255, 255, 255, 0.5);
            }
            button {
                width: 100%;
                padding: 15px;
                background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
                border: none;
                border-radius: 10px;
                color: white;
                font-size: 18px;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s;
                margin-top: 10px;
            }
            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(255, 107, 53, 0.3);
            }
            .info {
                text-align: center;
                margin-top: 30px;
                font-size: 0.9em;
                color: rgba(255, 255, 255, 0.6);
            }
            .error {
                background: rgba(244, 67, 54, 0.1);
                border: 1px solid rgba(244, 67, 54, 0.3);
                color: #ff6b6b;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 20px;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="logo">🎰</div>
            <h2>Imperio Rapidinhas</h2>
            {% if error %}
            <div class="error">{{ error }}</div>
            {% endif %}
            <form method="POST">
                <div class="form-group">
                    <input type="text" name="username" placeholder="Usuário" required autofocus>
                </div>
                <div class="form-group">
                    <input type="password" name="password" placeholder="Senha" required>
                </div>
                <button type="submit">Entrar</button>
            </form>
            <div class="info">
                Login padrão: admin / admin123
            </div>
        </div>
    </body>
    </html>
    """
    
    DASHBOARD_HTML = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard - Imperio Rapidinhas</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                background: #0a0a0a;
                color: white;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            .header {
                background: rgba(255, 107, 53, 0.1);
                backdrop-filter: blur(10px);
                border-bottom: 1px solid rgba(255, 107, 53, 0.3);
                padding: 20px;
                position: sticky;
                top: 0;
                z-index: 100;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            h1 {
                font-size: 2em;
                font-weight: 300;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .actions {
                display: flex;
                gap: 10px;
                margin: 30px 0;
                flex-wrap: wrap;
            }
            .btn {
                background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
                color: white;
                text-decoration: none;
                padding: 12px 24px;
                border-radius: 8px;
                display: inline-flex;
                align-items: center;
                gap: 8px;
                transition: all 0.3s;
                border: none;
                cursor: pointer;
                font-size: 16px;
            }
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(255, 107, 53, 0.3);
            }
            .btn-secondary {
                background: rgba(255, 255, 255, 0.1);
            }
            .metrics {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            .metric-card {
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                padding: 25px;
                transition: all 0.3s;
            }
            .metric-card:hover {
                transform: translateY(-5px);
                border-color: rgba(255, 107, 53, 0.5);
            }
            .metric-label {
                color: rgba(255, 255, 255, 0.6);
                font-size: 0.9em;
                margin-bottom: 10px;
            }
            .metric-value {
                font-size: 2.5em;
                font-weight: bold;
                background: linear-gradient(135deg, #ff6b35, #f7931e);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            .table-container {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 15px;
                overflow: hidden;
                margin-top: 30px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th {
                background: rgba(255, 107, 53, 0.2);
                padding: 15px;
                text-align: left;
                font-weight: 600;
            }
            td {
                padding: 15px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }
            tr:hover {
                background: rgba(255, 255, 255, 0.03);
            }
            .loading {
                text-align: center;
                padding: 50px;
                color: rgba(255, 255, 255, 0.5);
            }
            .spinner {
                display: inline-block;
                width: 40px;
                height: 40px;
                border: 3px solid rgba(255, 255, 255, 0.1);
                border-top-color: #ff6b35;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            .status {
                display: inline-flex;
                align-items: center;
                gap: 5px;
                padding: 5px 10px;
                border-radius: 20px;
                font-size: 0.85em;
            }
            .status-success {
                background: rgba(76, 175, 80, 0.2);
                color: #4caf50;
            }
            .status-info {
                background: rgba(33, 150, 243, 0.2);
                color: #2196f3;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="container">
                <h1>🎰 Dashboard - Imperio Rapidinhas</h1>
            </div>
        </div>
        
        <div class="container">
            <div class="actions">
                <button class="btn" onclick="startCapture()">
                    🔄 Capturar Dados
                </button>
                <a href="/api/latest-data" class="btn btn-secondary" target="_blank">
                    📊 Ver JSON
                </a>
                <a href="/logout" class="btn btn-secondary">
                    🚪 Sair
                </a>
            </div>
            
            <div id="content">
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Carregando dados...</p>
                </div>
            </div>
        </div>
        
        <script>
            function startCapture() {
                if (!confirm('Iniciar captura de dados?')) return;
                
                fetch('/api/capture')
                    .then(r => r.json())
                    .then(data => {
                        alert(data.status || data.error || 'Captura iniciada!');
                        setTimeout(() => loadData(), 5000);
                    })
                    .catch(e => alert('Erro: ' + e));
            }
            
            function formatCurrency(value) {
                return new Intl.NumberFormat('pt-BR', {
                    style: 'currency',
                    currency: 'BRL'
                }).format(value);
            }
            
            function loadData() {
                fetch('/api/latest-data')
                    .then(r => r.json())
                    .then(data => {
                        const content = document.getElementById('content');
                        
                        if (data.error) {
                            content.innerHTML = `
                                <div style="text-align: center; padding: 50px;">
                                    <h2>Nenhum dado disponível</h2>
                                    <p style="color: rgba(255,255,255,0.6); margin-top: 10px;">
                                        Execute uma captura para começar
                                    </p>
                                </div>
                            `;
                            return;
                        }
                        
                        const resumo = data.resumo_geral || {};
                        const rifas = data.rifas || [];
                        
                        content.innerHTML = `
                            <div class="metrics">
                                <div class="metric-card">
                                    <div class="metric-label">Total de Rifas</div>
                                    <div class="metric-value">${resumo.total_rifas || 0}</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-label">Arrecadação Total</div>
                                    <div class="metric-value">${formatCurrency(resumo.arrecadado_total || 0)}</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-label">Títulos Vendidos</div>
                                    <div class="metric-value">${(resumo.titulos_total || 0).toLocaleString('pt-BR')}</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-label">Ticket Médio</div>
                                    <div class="metric-value">${formatCurrency(resumo.ticket_medio_geral || 0)}</div>
                                </div>
                            </div>
                            
                            <h2 style="margin: 30px 0 20px;">Detalhamento por Rifa</h2>
                            
                            <div class="table-container">
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Título</th>
                                            <th>Status</th>
                                            <th>Vendas</th>
                                            <th>Títulos</th>
                                            <th>Arrecadação</th>
                                            <th>Ticket Médio</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${rifas.map(rifa => `
                                            <tr>
                                                <td>${rifa.titulo || 'Sem título'}</td>
                                                <td>
                                                    <span class="status ${rifa.status === 'Ativo' ? 'status-success' : 'status-info'}">
                                                        ${rifa.status || 'Desconhecido'}
                                                    </span>
                                                </td>
                                                <td>${(rifa.vendas_total || 0).toLocaleString('pt-BR')}</td>
                                                <td>${(rifa.titulos_total || 0).toLocaleString('pt-BR')}</td>
                                                <td>${formatCurrency(rifa.arrecadado_total || 0)}</td>
                                                <td>${formatCurrency(rifa.ticket_medio || 0)}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                            
                            <p style="text-align: center; margin-top: 30px; color: rgba(255,255,255,0.5);">
                                Última atualização: ${new Date().toLocaleString('pt-BR')}
                            </p>
                        `;
                    })
                    .catch(error => {
                        document.getElementById('content').innerHTML = 
                            '<p style="color: #ff6b6b; text-align: center;">Erro ao carregar dados: ' + error + '</p>';
                    });
            }
            
            // Carrega dados ao iniciar
            loadData();
            
            // Atualiza a cada 30 segundos
            setInterval(loadData, 30000);
        </script>
    </body>
    </html>
    """
    
    @app.route('/')
    def index():
        return redirect(url_for('login'))
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        error = None
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            if username == 'admin' and password == 'admin123':
                return redirect(url_for('dashboard'))
            else:
                error = 'Usuário ou senha inválidos'
        
        return render_template_string(LOGIN_HTML, error=error)
    
    @app.route('/dashboard')
    def dashboard():
        return render_template_string(DASHBOARD_HTML)
    
    @app.route('/logout')
    def logout():
        return redirect(url_for('login'))
    
    @app.route('/api/latest-data')
    def api_latest_data():
        try:
            data_dir = Path('data/captures')
            if not data_dir.exists():
                data_dir = Path('data')  # Tenta pasta data diretamente
            
            if not data_dir.exists():
                return jsonify({'error': 'Nenhum dado disponível'}), 404
            
            # Procura arquivos JSON
            json_files = list(data_dir.glob('*.json'))
            if not json_files and data_dir.name == 'captures':
                # Tenta na pasta data
                json_files = list(data_dir.parent.glob('*.json'))
            
            if not json_files:
                return jsonify({'error': 'Nenhum dado disponível'}), 404
            
            # Pega o arquivo mais recente
            latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return jsonify(data)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/capture')
    def api_capture():
        try:
            # Procura arquivo de captura
            capture_files = [
                'app/legacy/capture_legacy.py',
                'capture_complete.py',
                'captura.py'
            ]
            
            capture_script = None
            for cf in capture_files:
                if Path(cf).exists():
                    capture_script = cf
                    break
            
            if not capture_script:
                return jsonify({'error': 'Sistema de captura não encontrado'}), 404
            
            # Executa captura em processo separado
            if os.name == 'nt':  # Windows
                subprocess.Popen([sys.executable, capture_script], 
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen([sys.executable, capture_script])
            
            return jsonify({'status': 'Captura iniciada! Aguarde alguns minutos.'})
            
        except Exception as e:
            return jsonify({'error': f'Erro ao iniciar captura: {str(e)}'}), 500
    
    return app, None
