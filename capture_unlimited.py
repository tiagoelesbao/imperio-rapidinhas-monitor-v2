#!/usr/bin/env python3
"""
Sistema de Captura Imperio Rapidinhas - Versão Hoje em Diante
Captura apenas dados de ontem, hoje e continua acumulando para o futuro
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoAlertPresentException, TimeoutException, NoSuchElementException
import json
import time
import re
from datetime import datetime, timedelta
import os
from pathlib import Path
import sys

# Força UTF-8 no Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class ImperioCapturaTodayForward:
    def __init__(self, config_file='./config/config.json'):
        """Inicializa o sistema de captura"""
        self.config = self.load_config(config_file)
        self.driver = None
        self.data_dir = Path('data/captures')
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def load_config(self, config_file):
        """Carrega configurações"""
        config_path = Path(config_file)
        
        if not config_path.exists():
            config_path.parent.mkdir(parents=True, exist_ok=True)
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
            
            print("\n⚠️ CONFIGURAÇÃO NECESSÁRIA!")
            print("=" * 50)
            username = input("Digite seu usuário do Imperio Rapidinhas: ")
            password = input("Digite sua senha: ")
            
            default_config['imperio']['username'] = username
            default_config['imperio']['password'] = password
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            
            print("✅ Configuração salva!")
            return default_config
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def log(self, message):
        """Print com timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {message}")
    
    def setup_driver(self, headless=False):
        """Configura o driver do Chrome"""
        self.log("🔧 Configurando navegador...")
        
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        if headless:
            options.add_argument('--headless')
            self.log("Modo headless ativado")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_page_load_timeout(self.config['capture']['timeout'])
            self.log("✅ Navegador configurado!")
        except Exception as e:
            self.log(f"❌ Erro ao configurar navegador: {e}")
            raise
    
    def handle_alert(self):
        """Trata alerts se existirem"""
        try:
            alert = self.driver.switch_to.alert
            alert_text = alert.text
            self.log(f"📢 Alert: '{alert_text}'")
            alert.accept()
            time.sleep(1)
            return True
        except NoAlertPresentException:
            return False
    
    def wait_and_find(self, by, value, timeout=10):
        """Aguarda e encontra elemento"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            return None
    
    def login(self):
        """Realiza login no sistema"""
        self.log("🔐 Fazendo login...")
        
        try:
            self.driver.get(f"{self.config['imperio']['base_url']}/auth")
            time.sleep(3)
            
            # Aguarda campos de login
            username_field = self.wait_and_find(By.NAME, "username")
            password_field = self.driver.find_element(By.NAME, "password")
            
            if not username_field:
                raise Exception("Campos de login não encontrados")
            
            # Preenche credenciais
            username_field.clear()
            username_field.send_keys(self.config['imperio']['username'])
            password_field.clear()
            password_field.send_keys(self.config['imperio']['password'])
            
            # Submete formulário
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            time.sleep(3)
            self.handle_alert()
            
            # Verifica sucesso do login
            if "admin" in self.driver.current_url or "dashboard" in self.driver.current_url:
                self.log("✅ Login realizado com sucesso!")
                return True
                
        except Exception as e:
            self.log(f"❌ Erro no login: {e}")
            
        return False
    
    def parse_money(self, text):
        """Converte string monetária para float"""
        if not text:
            return 0.0
        
        # Remove tudo exceto números, vírgula e ponto
        clean = re.sub(r'[^\d,.-]', '', str(text))
        if not clean:
            return 0.0
            
        # Converte formato brasileiro (1.234,56) para float
        clean = clean.replace('.', '').replace(',', '.')
        
        try:
            return float(clean)
        except:
            return 0.0
    
    def extract_rifa_info(self, row_element):
        """Extrai informações de uma linha da tabela de rifas"""
        info = {
            'checkbox_value': '',
            'data_token': '',
            'id': '',
            'titulo': '',
            'status': 'Desconhecido',
            'vendas_total': 0,
            'titulos_total': 0,
            'arrecadado_total': 0.0,
            'ticket_medio': 0.0,
            'percentual_vendido': 0.0,
            'data_captura': datetime.now().isoformat()
        }
        
        try:
            # Busca checkbox
            try:
                checkbox = row_element.find_element(By.CSS_SELECTOR, "input[type='checkbox'][name='rifa[]']")
                info['checkbox_value'] = checkbox.get_attribute('value') or ''
                info['data_token'] = checkbox.get_attribute('data-token') or ''
            except:
                pass
            
            # Busca células da linha
            cells = row_element.find_elements(By.TAG_NAME, "td")
            
            if len(cells) >= 7:  # Estrutura esperada da tabela
                # Célula 0: Checkbox (já processado)
                
                # Célula 1: ID
                id_text = cells[1].text.strip()
                info['id'] = id_text
                
                # Célula 2: Título
                titulo_text = cells[2].text.strip()
                info['titulo'] = titulo_text
                
                # Célula 3: Status
                try:
                    status_elem = cells[3].find_element(By.CSS_SELECTOR, "span.badge, span.status")
                    info['status'] = status_elem.text.strip()
                except:
                    info['status'] = cells[3].text.strip()
                
                # Célula 4: Vendas
                vendas_text = cells[4].text.strip()
                if vendas_text:
                    numbers = re.findall(r'\d+', vendas_text)
                    if numbers:
                        info['vendas_total'] = int(numbers[0])
                
                # Célula 5: Títulos
                titulos_text = cells[5].text.strip()
                if titulos_text:
                    numbers = re.findall(r'\d+', titulos_text)
                    if numbers:
                        info['titulos_total'] = int(numbers[0])
                
                # Célula 6: Arrecadação
                arrecadacao_text = cells[6].text.strip()
                info['arrecadado_total'] = self.parse_money(arrecadacao_text)
                
                # Célula 7: Ticket Médio (se existir)
                if len(cells) > 7:
                    ticket_text = cells[7].text.strip()
                    info['ticket_medio'] = self.parse_money(ticket_text)
                elif info['vendas_total'] > 0 and info['arrecadado_total'] > 0:
                    info['ticket_medio'] = info['arrecadado_total'] / info['vendas_total']
            else:
                # Tenta extrair por texto completo
                full_text = row_element.text
                
                # ID
                id_match = re.search(r'#(\d{4,})', full_text)
                if id_match:
                    info['id'] = f"#{id_match.group(1)}"
                
                # Título
                titulo_match = re.search(r'(\d+º?\s*RAPIDINHA.*?R\$[\d.,]+)', full_text, re.IGNORECASE)
                if titulo_match:
                    info['titulo'] = titulo_match.group(1)
                
                # Status
                if 'ativo' in full_text.lower():
                    info['status'] = 'Ativo'
                elif 'finalizado' in full_text.lower() or 'concluído' in full_text.lower():
                    info['status'] = 'Finalizado'
                
                # Valores monetários
                money_matches = re.findall(r'R\$\s*([\d.,]+)', full_text)
                if money_matches:
                    valores = [self.parse_money(m) for m in money_matches]
                    if valores:
                        info['arrecadado_total'] = max(valores)  # Geralmente o maior é o total
        
        except Exception as e:
            self.log(f"⚠️ Erro ao extrair dados: {e}")
        
        # Se não tem título, cria um genérico
        if not info['titulo'] and info['id']:
            info['titulo'] = f"Rifa {info['id']}"
        elif not info['titulo'] and info['checkbox_value']:
            info['titulo'] = f"Rifa #{info['checkbox_value']}"
        
        # Calcula percentual vendido
        if info['titulos_total'] > 0 and info['vendas_total'] > 0:
            info['percentual_vendido'] = (info['vendas_total'] / info['titulos_total']) * 100
        
        return info
    
    def capture_all_rifas(self):
        """Captura todas as rifas de todas as páginas"""
        self.log("📊 Iniciando captura de todas as rifas...")
        
        # Navega para página de rifas
        self.driver.get(f"{self.config['imperio']['base_url']}/admin/rifas")
        time.sleep(3)
        self.handle_alert()
        
        all_rifas = []
        page = 1
        
        while True:
            self.log(f"\n📄 Processando página {page}...")
            
            # Busca tabela de rifas
            try:
                # Aguarda tabela carregar
                table = self.wait_and_find(By.CSS_SELECTOR, "table.table, table#rifas-table", timeout=5)
                if not table:
                    self.log("⚠️ Tabela não encontrada, tentando outros seletores...")
                    table = self.wait_and_find(By.TAG_NAME, "table", timeout=5)
                
                if not table:
                    self.log("❌ Nenhuma tabela encontrada!")
                    break
                
                # Busca linhas da tabela
                rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
                
                if not rows:
                    self.log("⚠️ Nenhuma linha encontrada na tabela")
                    break
                
                self.log(f"✅ Encontradas {len(rows)} rifas na página {page}")
                
                # Processa cada linha
                for i, row in enumerate(rows):
                    try:
                        # Verifica se é uma linha válida (não é mensagem de "sem dados")
                        if "nenhuma rifa" in row.text.lower() or "sem dados" in row.text.lower():
                            continue
                        
                        rifa_info = self.extract_rifa_info(row)
                        
                        # Só adiciona se tem alguma informação válida
                        if rifa_info['titulo'] or rifa_info['id'] or rifa_info['checkbox_value']:
                            all_rifas.append(rifa_info)
                            self.log(f"   ✅ [{len(all_rifas)}] {rifa_info['titulo']} - R$ {rifa_info['arrecadado_total']:,.2f}")
                        
                    except Exception as e:
                        self.log(f"   ⚠️ Erro ao processar linha {i+1}: {e}")
                
            except Exception as e:
                self.log(f"❌ Erro ao processar página {page}: {e}")
                break
            
            # Busca botão de próxima página
            try:
                # Diferentes possibilidades de paginação
                next_selectors = [
                    "a.page-link:contains('Próxima')",
                    "a.page-link:contains('>')",
                    "button:contains('Próxima')",
                    "a[rel='next']",
                    "li.page-item:not(.disabled) a[aria-label='Next']"
                ]
                
                next_button = None
                for selector in next_selectors:
                    try:
                        # Tenta com JavaScript
                        next_button = self.driver.execute_script(
                            f"return document.querySelector('{selector}')"
                        )
                        if next_button:
                            break
                    except:
                        pass
                
                # Se não encontrou com JS, tenta com Selenium
                if not next_button:
                    try:
                        next_button = self.driver.find_element(By.XPATH, 
                            "//a[contains(@class, 'page-link') and (contains(text(), '>') or contains(text(), 'Próxima'))]"
                        )
                    except:
                        pass
                
                if next_button and next_button.is_enabled():
                    # Verifica se não está desabilitado
                    parent_li = next_button.find_element(By.XPATH, "..")
                    if 'disabled' not in parent_li.get_attribute('class'):
                        self.driver.execute_script("arguments[0].click();", next_button)
                        time.sleep(3)
                        page += 1
                        continue
                
                # Se chegou aqui, não há mais páginas
                self.log("✅ Todas as páginas processadas!")
                break
                
            except Exception as e:
                self.log(f"ℹ️ Fim da paginação ou erro: {e}")
                break
            
            # Limite de segurança
            if page > 50:
                self.log("⚠️ Limite de páginas atingido (50)")
                break
        
        self.log(f"\n✅ Total de rifas capturadas: {len(all_rifas)}")
        return all_rifas
    
    def save_data(self, rifas_data):
        """Salva dados capturados"""
        timestamp = datetime.now()
        
        # Calcula resumo geral
        resumo = {
            'total_rifas': len(rifas_data),
            'rifas_ativas': len([r for r in rifas_data if r.get('status') == 'Ativo']),
            'rifas_finalizadas': len([r for r in rifas_data if r.get('status') in ['Finalizado', 'Concluído']]),
            'vendas_total': sum(r.get('vendas_total', 0) for r in rifas_data),
            'titulos_total': sum(r.get('titulos_total', 0) for r in rifas_data),
            'arrecadado_total': sum(r.get('arrecadado_total', 0) for r in rifas_data),
            'ticket_medio_geral': 0.0,
            'percentual_vendido_geral': 0.0
        }
        
        # Calcula médias
        if resumo['vendas_total'] > 0:
            resumo['ticket_medio_geral'] = resumo['arrecadado_total'] / resumo['vendas_total']
        
        if resumo['titulos_total'] > 0:
            resumo['percentual_vendido_geral'] = (resumo['vendas_total'] / resumo['titulos_total']) * 100
        
        # Estrutura completa
        data = {
            'captura': {
                'timestamp': timestamp.isoformat(),
                'timestamp_unix': timestamp.timestamp(),
                'data': timestamp.strftime('%Y-%m-%d'),
                'hora': timestamp.strftime('%H:%M:%S'),
                'versao': 'today_forward_1.0'
            },
            'resumo_geral': resumo,
            'rifas': rifas_data
        }
        
        # Salva arquivo principal
        filename = f"captura_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.data_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self.log(f"\n💾 Dados salvos em: {filepath}")
        
        # Salva também um resumo do dia
        self.update_daily_summary(resumo, timestamp)
        
        return filepath
    
    def update_daily_summary(self, resumo, timestamp):
        """Atualiza resumo diário acumulado"""
        daily_file = self.data_dir / f"resumo_diario_{timestamp.strftime('%Y%m%d')}.json"
        
        if daily_file.exists():
            with open(daily_file, 'r', encoding='utf-8') as f:
                daily_data = json.load(f)
        else:
            daily_data = {
                'data': timestamp.strftime('%Y-%m-%d'),
                'primeira_captura': timestamp.isoformat(),
                'capturas': []
            }
        
        # Adiciona captura atual
        daily_data['ultima_captura'] = timestamp.isoformat()
        daily_data['capturas'].append({
            'hora': timestamp.strftime('%H:%M:%S'),
            'resumo': resumo
        })
        
        # Calcula totais do dia (usa última captura como referência)
        daily_data['resumo_final_dia'] = resumo
        
        with open(daily_file, 'w', encoding='utf-8') as f:
            json.dump(daily_data, f, ensure_ascii=False, indent=2)
        
        self.log(f"📊 Resumo diário atualizado: {daily_file.name}")
    
    def display_summary(self, rifas_data):
        """Exibe resumo dos dados capturados"""
        print("\n" + "="*80)
        print("📊 RESUMO DA CAPTURA")
        print("="*80)
        
        total_rifas = len(rifas_data)
        rifas_ativas = len([r for r in rifas_data if r.get('status') == 'Ativo'])
        total_arrecadado = sum(r.get('arrecadado_total', 0) for r in rifas_data)
        total_vendas = sum(r.get('vendas_total', 0) for r in rifas_data)
        
        print(f"\n📈 ESTATÍSTICAS GERAIS:")
        print(f"   Total de rifas: {total_rifas}")
        print(f"   Rifas ativas: {rifas_ativas}")
        print(f"   Total de vendas: {total_vendas:,}")
        print(f"   Arrecadação total: R$ {total_arrecadado:,.2f}")
        
        if total_vendas > 0:
            ticket_medio = total_arrecadado / total_vendas
            print(f"   Ticket médio geral: R$ {ticket_medio:.2f}")
        
        # Top 5 rifas
        rifas_com_valor = [r for r in rifas_data if r.get('arrecadado_total', 0) > 0]
        if rifas_com_valor:
            print(f"\n🏆 TOP 5 RIFAS POR ARRECADAÇÃO:")
            sorted_rifas = sorted(rifas_com_valor, key=lambda x: x.get('arrecadado_total', 0), reverse=True)[:5]
            
            for i, rifa in enumerate(sorted_rifas, 1):
                print(f"\n   {i}. {rifa['titulo']}")
                print(f"      Arrecadado: R$ {rifa.get('arrecadado_total', 0):,.2f}")
                print(f"      Vendas: {rifa.get('vendas_total', 0):,}")
                if rifa.get('percentual_vendido', 0) > 0:
                    print(f"      Vendido: {rifa.get('percentual_vendido', 0):.1f}%")
                print(f"      Status: {rifa.get('status', 'Desconhecido')}")
    
    def run(self, headless=False):
        """Executa captura completa"""
        print("\n🎰 SISTEMA DE CAPTURA - IMPÉRIO RAPIDINHAS")
        print("="*80)
        print("📌 Modo: Captura de hoje em diante")
        print("📅 Data: " + datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
        print("="*80)
        
        try:
            # Setup
            self.setup_driver(headless)
            
            # Login
            if not self.login():
                raise Exception("Falha no login")
            
            # Captura todas as rifas
            rifas_data = self.capture_all_rifas()
            
            if not rifas_data:
                self.log("⚠️ Nenhuma rifa foi capturada!")
                return None
            
            # Salva resultados
            filepath = self.save_data(rifas_data)
            
            # Exibe resumo
            self.display_summary(rifas_data)
            
            self.log("\n✅ Captura concluída com sucesso!")
            
            return filepath
            
        except Exception as e:
            self.log(f"\n❌ Erro durante captura: {e}")
            import traceback
            traceback.print_exc()
            return None
            
        finally:
            if self.driver:
                self.log("\n🔚 Fechando navegador...")
                self.driver.quit()

def main():
    """Função principal"""
    import sys
    
    capture = ImperioCapturaTodayForward()
    
    # Verifica argumentos
    headless = '--headless' in sys.argv
    
    capture.run(headless=headless)
    
    if not headless:
        input("\nPressione ENTER para fechar...")

if __name__ == "__main__":
    main()