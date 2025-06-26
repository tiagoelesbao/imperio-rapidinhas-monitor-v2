#!/usr/bin/env python3
"""
Script para resetar completamente a configuração
"""
import json
import shutil
from pathlib import Path
from datetime import datetime

def reset_config():
    """Reseta arquivo de configuração para o padrão"""
    config_path = Path('./config/config.json')
    
    print("⚠️  RESET DE CONFIGURAÇÃO")
    print("="*50)
    print("Este script irá:")
    print("1. Fazer backup da configuração atual (se existir)")
    print("2. Criar uma nova configuração padrão")
    print("3. Solicitar suas credenciais")
    print()
    
    response = input("Deseja continuar? (S/N): ").strip().upper()
    if response != 'S':
        print("Operação cancelada.")
        return
    
    # Backup se existir
    if config_path.exists():
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = config_path.parent / f'config_backup_{timestamp}.json'
        shutil.copy2(config_path, backup_path)
        print(f"\n✅ Backup criado: {backup_path}")
    
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
    
    # Solicita credenciais
    print("\n📝 CONFIGURAÇÃO DE CREDENCIAIS")
    print("-"*40)
    
    username = input("Digite seu usuário do Imperio Rapidinhas: ").strip()
    password = input("Digite sua senha: ").strip()
    
    if not username or not password:
        print("\n❌ Usuário e senha são obrigatórios!")
        return
    
    default_config['imperio']['username'] = username
    default_config['imperio']['password'] = password
    
    # Pergunta sobre configurações avançadas
    print("\n⚙️  CONFIGURAÇÕES AVANÇADAS (pressione ENTER para usar padrão)")
    print("-"*40)
    
    timeout_str = input(f"Timeout de página em segundos [{default_config['capture']['timeout']}]: ").strip()
    if timeout_str.isdigit():
        default_config['capture']['timeout'] = int(timeout_str)
    
    wait_str = input(f"Espera entre ações em segundos [{default_config['capture']['wait_between_actions']}]: ").strip()
    if wait_str.isdigit():
        default_config['capture']['wait_between_actions'] = int(wait_str)
    
    # Cria diretório se não existir
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Salva nova configuração
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=2, ensure_ascii=False)
    
    print("\n✅ Nova configuração criada com sucesso!")
    print(f"   Arquivo: {config_path.absolute()}")
    
    # Mostra resumo
    print("\n📊 RESUMO DA CONFIGURAÇÃO:")
    print(f"   Usuário: {default_config['imperio']['username']}")
    print(f"   URL: {default_config['imperio']['base_url']}")
    print(f"   Timeout: {default_config['capture']['timeout']}s")
    print(f"   Espera entre ações: {default_config['capture']['wait_between_actions']}s")
    
    print("\n✅ Configuração pronta! Você já pode executar o capture_unlimited.py")

if __name__ == "__main__":
    reset_config()
    input("\nPressione ENTER para fechar...")