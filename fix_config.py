#!/usr/bin/env python3
"""
Script para corrigir arquivo de configuração existente
"""
import json
from pathlib import Path

def fix_config():
    """Corrige arquivo de configuração existente"""
    config_path = Path('./config/config.json')
    
    if not config_path.exists():
        print("❌ Arquivo de configuração não encontrado!")
        print("   Execute o capture_unlimited.py para criar um novo.")
        return
    
    print("🔧 Verificando arquivo de configuração...")
    
    try:
        # Carrega configuração existente
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Estrutura padrão
        default_config = {
            'imperio': {
                'username': '',
                'password': '',
                'base_url': 'https://dashboard.imperiorapidinhas.me'
            },
            'capture': {
                'timeout': 30,
                'wait_between_actions': 2
            }
        }
        
        updated = False
        
        # Verifica e corrige estrutura
        if 'imperio' not in config:
            config['imperio'] = default_config['imperio']
            updated = True
            print("⚠️ Adicionada seção 'imperio'")
        
        if 'capture' not in config:
            config['capture'] = default_config['capture']
            updated = True
            print("⚠️ Adicionada seção 'capture'")
        
        # Verifica campos individuais
        for key, value in default_config['imperio'].items():
            if key not in config['imperio']:
                config['imperio'][key] = value
                updated = True
                print(f"⚠️ Adicionado campo 'imperio.{key}'")
        
        for key, value in default_config['capture'].items():
            if key not in config['capture']:
                config['capture'][key] = value
                updated = True
                print(f"⚠️ Adicionado campo 'capture.{key}'")
        
        # Salva configuração corrigida
        if updated:
            # Backup do arquivo original
            backup_path = config_path.with_suffix('.json.bak')
            config_path.rename(backup_path)
            print(f"📋 Backup criado: {backup_path}")
            
            # Salva configuração corrigida
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            print("✅ Configuração corrigida com sucesso!")
        else:
            print("✅ Configuração já está correta!")
        
        # Mostra status
        print("\n📊 Status da configuração:")
        print(f"   Usuário: {config['imperio']['username'] or '(não configurado)'}")
        print(f"   URL: {config['imperio']['base_url']}")
        print(f"   Timeout: {config['capture']['timeout']}s")
        
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao ler arquivo JSON: {e}")
        print("   O arquivo pode estar corrompido.")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    fix_config()
    input("\nPressione ENTER para fechar...")