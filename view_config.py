#!/usr/bin/env python3
"""
Script para visualizar configuração atual
"""
import json
from pathlib import Path
import pprint

def view_config():
    """Visualiza arquivo de configuração atual"""
    config_path = Path('./config/config.json')
    
    print("🔍 VISUALIZADOR DE CONFIGURAÇÃO")
    print("="*50)
    
    if not config_path.exists():
        print("❌ Arquivo de configuração não encontrado!")
        print(f"   Caminho esperado: {config_path.absolute()}")
        return
    
    try:
        # Carrega e exibe configuração
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"\n📁 Arquivo: {config_path.absolute()}")
        print(f"📊 Tamanho: {config_path.stat().st_size} bytes")
        print("\n📋 Conteúdo atual:\n")
        
        # Pretty print
        pp = pprint.PrettyPrinter(indent=2, width=80)
        pp.pprint(config)
        
        # Verifica estrutura
        print("\n✅ Verificação de estrutura:")
        
        # Chaves principais
        required_keys = ['imperio', 'capture']
        for key in required_keys:
            if key in config:
                print(f"   ✓ Seção '{key}' presente")
            else:
                print(f"   ✗ Seção '{key}' AUSENTE!")
        
        # Subcampos imperio
        if 'imperio' in config:
            imperio_keys = ['username', 'password', 'base_url']
            for key in imperio_keys:
                if key in config['imperio']:
                    value = config['imperio'][key]
                    if key == 'password' and value:
                        value = '*' * len(value)  # Oculta senha
                    print(f"   ✓ imperio.{key}: {value or '(vazio)'}")
                else:
                    print(f"   ✗ imperio.{key}: AUSENTE!")
        
        # Subcampos capture
        if 'capture' in config:
            capture_keys = ['timeout', 'wait_between_actions']
            for key in capture_keys:
                if key in config['capture']:
                    print(f"   ✓ capture.{key}: {config['capture'][key]}")
                else:
                    print(f"   ✗ capture.{key}: AUSENTE!")
        
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao decodificar JSON: {e}")
        print("\nTentando mostrar conteúdo bruto:")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(content[:500])  # Mostra primeiros 500 caracteres
            if len(content) > 500:
                print("... (truncado)")
        except Exception as e2:
            print(f"Erro ao ler arquivo: {e2}")
    
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    view_config()
    input("\nPressione ENTER para fechar...")