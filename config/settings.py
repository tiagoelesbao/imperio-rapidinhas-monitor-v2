"""
Configurações do sistema
"""
import os
import json
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Diretórios base
BASE_DIR = Path(__file__).parent.parent
CONFIG_DIR = BASE_DIR / 'config'
DATA_DIR = BASE_DIR / 'data'
LOGS_DIR = BASE_DIR / 'logs'

# Criar diretórios se não existirem
for directory in [CONFIG_DIR, DATA_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

class Config:
    """Configuração base"""
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{DATA_DIR}/imperio.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Login
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    SESSION_PROTECTION = 'strong'
    
    # Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = DATA_DIR / 'uploads'
    
    # Captura
    IMPERIO_BASE_URL = 'https://dashboard.imperiorapidinhas.me'
    CAPTURE_TIMEOUT = 300  # 5 minutos
    CAPTURE_RETRY_ATTEMPTS = 3
    
    # WebSocket
    SOCKETIO_ASYNC_MODE = 'eventlet'
    
    # Cache
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Logs
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Email (para notificações)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Scheduler
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = 'America/Sao_Paulo'
    
    # Analytics
    ANALYTICS_RETENTION_DAYS = 90
    REPORT_RETENTION_DAYS = 180
    
    @staticmethod
    def load_credentials():
        """Carrega credenciais do arquivo config.json"""
        config_file = CONFIG_DIR / 'config.json'
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        return {}
    
    @staticmethod
    def save_credentials(credentials):
        """Salva credenciais no arquivo config.json"""
        config_file = CONFIG_DIR / 'config.json'
        with open(config_file, 'w') as f:
            json.dump(credentials, f, indent=2)

class DevelopmentConfig(Config):
    """Configuração de desenvolvimento"""
    DEBUG = True
    TESTING = False
    
    # Usar banco SQLite local
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATA_DIR}/imperio_dev.db'
    
    # Logs mais detalhados
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Configuração de produção"""
    DEBUG = False
    TESTING = False
    
    # Forçar HTTPS
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Database de produção (pode ser PostgreSQL)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{DATA_DIR}/imperio_prod.db'
    
    # Cache Redis se disponível
    if os.environ.get('REDIS_URL'):
        CACHE_TYPE = 'redis'
        CACHE_REDIS_URL = os.environ.get('REDIS_URL')

class TestingConfig(Config):
    """Configuração de testes"""
    TESTING = True
    WTF_CSRF_ENABLED = False
    
    # Banco em memória para testes
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Configurações disponíveis
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(env=None):
    """Retorna configuração baseada no ambiente"""
    if not env:
        env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])

# Configurações de captura
CAPTURE_CONFIG = {
    'imperio': {
        'username': '',
        'password': '',
        'base_url': 'https://dashboard.imperiorapidinhas.me'
    },
    'automation': {
        'auto_capture_enabled': False,
        'capture_interval_minutes': 60,
        'capture_times': ['08:00', '12:00', '18:00', '22:00'],
        'use_headless': True,
        'retry_on_failure': True,
        'notification_on_error': True
    },
    'selenium': {
        'driver': 'chrome',
        'headless': True,
        'window_size': '1920,1080',
        'page_load_timeout': 30,
        'implicit_wait': 10,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
}

# Configurações de relatórios
REPORT_CONFIG = {
    'formats': ['json', 'excel', 'pdf'],
    'default_format': 'excel',
    'include_charts': True,
    'company_info': {
        'name': 'Império Rapidinhas',
        'logo': 'static/img/logo.png',
        'address': '',
        'phone': '',
        'email': ''
    },
    'templates': {
        'daily': 'templates/reports/daily.html',
        'weekly': 'templates/reports/weekly.html',
        'monthly': 'templates/reports/monthly.html',
        'custom': 'templates/reports/custom.html'
    }
}

# Configurações de notificações
NOTIFICATION_CONFIG = {
    'enabled': True,
    'channels': ['email', 'webhook', 'dashboard'],
    'events': {
        'capture_success': True,
        'capture_failure': True,
        'low_performance': True,
        'high_performance': True,
        'system_error': True
    },
    'thresholds': {
        'low_performance': -10,  # % de queda
        'high_performance': 20,   # % de crescimento
        'error_count': 3          # erros consecutivos
    }
}

# Configurações de analytics
ANALYTICS_CONFIG = {
    'metrics': {
        'arrecadacao': {'enabled': True, 'precision': 2},
        'vendas': {'enabled': True, 'precision': 0},
        'titulos': {'enabled': True, 'precision': 0},
        'ticket_medio': {'enabled': True, 'precision': 2},
        'taxa_conversao': {'enabled': True, 'precision': 1},
        'crescimento': {'enabled': True, 'precision': 1}
    },
    'charts': {
        'timeline': {'type': 'area', 'height': 350},
        'top_rifas': {'type': 'bar', 'limit': 10},
        'hourly_pattern': {'type': 'line', 'height': 300},
        'weekly_pattern': {'type': 'heatmap', 'height': 250}
    },
    'insights': {
        'enabled': True,
        'auto_generate': True,
        'min_confidence': 0.7,
        'max_insights': 5
    }
}

# Configurações de segurança
SECURITY_CONFIG = {
    'password_min_length': 8,
    'password_require_uppercase': True,
    'password_require_numbers': True,
    'password_require_special': True,
    'max_login_attempts': 5,
    'lockout_duration': 300,  # 5 minutos
    'session_timeout': 3600,  # 1 hora
    'two_factor_enabled': False,
    'ip_whitelist': [],
    'ip_blacklist': []
}