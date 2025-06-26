#!/usr/bin/env python3
"""
Sistema de Captura Corrigido - Império Rapidinhas
Segue o fluxo correto: Lista de rifas → Data tokens → Relatórios detalhados
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
from datetime import datetime
import os
from pathlib import Path
import sys

# Força UTF-8 no Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class ImperioCapturaCorrected:
    def __init__(self, config_file='./config/config.json'):
        """Inicializa o sistema corrigido"""
        self.config = self.load_config(config_file)
        self.driver = None
        self.data_dir = Path('data/captures')
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.rifas_data = []
        self.detailed_reports = {}
        
    def load_config(self, config_file):
        """Carrega configurações com validação completa"""
        config_path = Path(config_file)
        
        # Estrutura padrão completa
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
        
        if not config_path.exists():
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
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
        
        # Carrega configuração existente
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Verifica e adiciona chaves faltantes
        updated = False
        
        if 'capture' not in config:
            config['capture'] = default_config['capture']
            updated = True
        
        if updated:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        
        return config
    
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
            
            timeout = self.config.get('capture', {}).get('timeout', 30)
            self.driver.set_page_load_timeout(timeout)
            
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
        
        clean = re.sub(r'[^\d,.-]', '', str(text))
        if not clean:
            return 0.0
            
        clean = clean.replace('.', '').replace(',', '.')
        
        try:
            return float(clean)
        except:
            return 0.0
    
    def parse_quantity(self, text):
        """Extrai quantidade de strings como '93 93%' ou '93'"""
        if not text:
            return 0
        
        match = re.match(r'(\d+)', str(text).strip())
        if match:
            return int(match.group(1))
        
        return 0
    
    def capture_rifas_list(self):
        """ETAPA 1: Captura lista de rifas com checkboxes e data-tokens"""
        self.log("\n📋 ETAPA 1: Capturando lista de rifas...")
        
        self.driver.get(f"{self.config['imperio']['base_url']}/admin/rifas")
        time.sleep(3)
        self.handle_alert()
        
        rifas = []
        page = 1
        
        while True:
            self.log(f"\n📄 Processando página {page}...")
            
            try:
                # Busca checkboxes - elemento chave para identificar rifas
                checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox'][name='rifa[]']")
                
                if not checkboxes:
                    self.log("⚠️ Nenhum checkbox encontrado na página")
                    
                    # Tenta buscar de outras formas
                    # Verifica se existe mensagem de "sem dados"
                    try:
                        body_text = self.driver.find_element(By.TAG_NAME, "body").text
                        if "nenhuma rifa" in body_text.lower() or "sem dados" in body_text.lower():
                            self.log("ℹ️ Página indica que não há rifas")
                            break
                    except:
                        pass
                    
                    # Tenta debug - salva screenshot
                    screenshot_path = f"debug_page_{page}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    self.driver.save_screenshot(screenshot_path)
                    self.log(f"📸 Screenshot salvo: {screenshot_path}")
                    
                    break
                
                self.log(f"✅ Encontrados {len(checkboxes)} checkboxes")
                
                # Para cada checkbox, extrai informações
                for i, checkbox in enumerate(checkboxes):
                    try:
                        rifa_info = {
                            'index': len(rifas) + 1,
                            'checkbox_value': checkbox.get_attribute('value') or '',
                            'data_token': checkbox.get_attribute('data-token') or '',
                            'timestamp_captura': datetime.now().isoformat(),
                            'id': '',
                            'titulo': '',
                            'status': 'Desconhecido'
                        }
                        
                        # Validação do data-token
                        if not rifa_info['data_token']:
                            self.log(f"   ⚠️ Checkbox {i+1} sem data-token, pulando...")
                            continue
                        
                        # Tenta extrair mais informações do container pai
                        try:
                            # Busca a linha da tabela (TR) que contém o checkbox
                            row = checkbox.find_element(By.XPATH, "./ancestor::tr[1]")
                            cells = row.find_elements(By.TAG_NAME, "td")
                            
                            # Geralmente a estrutura é:
                            # TD 0: Checkbox
                            # TD 1: ID
                            # TD 2: Título
                            # TD 3: Status
                            # ... outras colunas
                            
                            if len(cells) >= 3:
                                # ID (segunda coluna)
                                if len(cells) > 1:
                                    id_text = cells[1].text.strip()
                                    if id_text:
                                        rifa_info['id'] = id_text
                                
                                # Título (terceira coluna)
                                if len(cells) > 2:
                                    titulo_text = cells[2].text.strip()
                                    if titulo_text:
                                        rifa_info['titulo'] = titulo_text
                                
                                # Status (quarta coluna)
                                if len(cells) > 3:
                                    status_text = cells[3].text.strip()
                                    if status_text:
                                        rifa_info['status'] = status_text
                            
                        except Exception as e:
                            # Se falhar, tenta extrair do texto geral
                            try:
                                container = checkbox.find_element(By.XPATH, "./ancestor::*[self::tr or self::div][1]")
                                text = container.text
                                
                                # Extrai ID
                                id_match = re.search(r'#(\d{4,})', text)
                                if id_match:
                                    rifa_info['id'] = f"#{id_match.group(1)}"
                                
                                # Extrai título
                                title_match = re.search(r'(\d+º?\s*RAPIDINHA.*?R\$[\d.,]+)', text, re.IGNORECASE)
                                if title_match:
                                    rifa_info['titulo'] = title_match.group(1)
                                
                                # Extrai status
                                if 'ativo' in text.lower():
                                    rifa_info['status'] = 'Ativo'
                                elif 'concluído' in text.lower() or 'concluido' in text.lower():
                                    rifa_info['status'] = 'Concluído'
                                elif 'finalizado' in text.lower():
                                    rifa_info['status'] = 'Finalizado'
                            except:
                                pass
                        
                        rifas.append(rifa_info)
                        self.log(f"   ✅ [{len(rifas)}] Token: {rifa_info['data_token'][:20]}... | ID: {rifa_info.get('id', 'N/A')}")
                        
                    except Exception as e:
                        self.log(f"   ⚠️ Erro ao processar checkbox {i+1}: {e}")
                
            except Exception as e:
                self.log(f"❌ Erro ao processar página {page}: {e}")
                break
            
            # Busca botão de próxima página
            try:
                # Tenta encontrar link/botão "Próxima" ou ">"
                next_button = None
                
                # Métodos diferentes para encontrar o botão
                selectors = [
                    "//a[contains(text(), 'Próxima')]",
                    "//a[contains(text(), '>')]",
                    "//li[@class='page-item']//a[contains(text(), '>')]",
                    "//ul[@class='pagination']//a[contains(text(), '>')]"
                ]
                
                for selector in selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        for elem in elements:
                            if elem.is_displayed() and elem.is_enabled():
                                # Verifica se não está desabilitado
                                parent_li = elem.find_element(By.XPATH, "./..")
                                if 'disabled' not in parent_li.get_attribute('class'):
                                    next_button = elem
                                    break
                    except:
                        continue
                    
                    if next_button:
                        break
                
                if next_button:
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    time.sleep(1)
                    self.driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(3)
                    page += 1
                    continue
                else:
                    self.log("✅ Todas as páginas processadas!")
                    break
                    
            except Exception as e:
                self.log(f"ℹ️ Fim da paginação: {e}")
                break
            
            # Limite de segurança
            if page > 50:
                self.log("⚠️ Limite de páginas atingido (50)")
                break
        
        self.rifas_data = rifas
        self.log(f"\n✅ Total de rifas capturadas: {len(rifas)}")
        return rifas
    
    def extract_title_from_breadcrumb(self):
        """Extrai título do breadcrumb da página"""
        try:
            breadcrumb = self.driver.find_element(By.CSS_SELECTOR, ".breadcrumb")
            if breadcrumb:
                items = breadcrumb.find_elements(By.CSS_SELECTOR, "li")
                for item in reversed(items):
                    text = item.text.strip()
                    if 'RAPIDINHA' in text.upper():
                        return text
        except:
            pass
        
        return ""
    
    def capture_detailed_report(self, rifa_info):
        """ETAPA 2: Captura relatório detalhado usando data-token"""
        token = rifa_info.get('data_token')
        if not token:
            return None
        
        url = f"{self.config['imperio']['base_url']}/admin/rifas/relatorios/{token}"
        
        try:
            self.log(f"   📊 Acessando relatório: {url}")
            self.driver.get(url)
            time.sleep(2)
            
            # Extrai título do breadcrumb se não tiver
            if not rifa_info.get('titulo'):
                titulo = self.extract_title_from_breadcrumb()
                if titulo:
                    rifa_info['titulo'] = titulo
                    self.log(f"      ✅ Título encontrado: {titulo}")
            
            report_data = {
                'token': token,
                'url': url,
                'titulo': rifa_info.get('titulo', ''),
                'id': rifa_info.get('id', ''),
                'checkbox_value': rifa_info.get('checkbox_value', ''),
                'dados_tabela': [],
                'resumo': {
                    'vendas_total': 0,
                    'titulos_total': 0,
                    'arrecadado_total': 0.0,
                    'ticket_medio_geral': 0.0,
                    'dias_com_vendas': 0,
                    'recusadas': 0
                }
            }
            
            # Procura pela tabela de vendas
            tables = self.driver.find_elements(By.CSS_SELECTOR, "table.table")
            
            for table in tables:
                headers_elements = table.find_elements(By.CSS_SELECTOR, "thead th")
                if not headers_elements:
                    continue
                
                headers = [h.text.strip().lower() for h in headers_elements]
                
                # Verifica se é a tabela correta (tem colunas de data e vendas)
                if any('data' in h for h in headers) and any('vendas' in h for h in headers):
                    self.log("      ✅ Tabela de vendas encontrada")
                    
                    # Mapeia índices das colunas
                    col_map = {
                        'data': next((i for i, h in enumerate(headers) if 'data' in h), -1),
                        'ticket': next((i for i, h in enumerate(headers) if 'ticket' in h or 'tícket' in h), -1),
                        'vendas': next((i for i, h in enumerate(headers) if 'vendas' in h), -1),
                        'titulos': next((i for i, h in enumerate(headers) if 'qtd' in h or 'título' in h), -1),
                        'total': next((i for i, h in enumerate(headers) if 'total' in h), -1)
                    }
                    
                    # Processa linhas
                    tbody = table.find_element(By.TAG_NAME, "tbody")
                    rows = tbody.find_elements(By.TAG_NAME, "tr")
                    
                    for row in rows:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= len(headers):
                            row_data = {}
                            
                            if col_map['data'] >= 0:
                                row_data['data'] = cells[col_map['data']].text.strip()
                            
                            if col_map['ticket'] >= 0:
                                row_data['ticket_medio'] = self.parse_money(cells[col_map['ticket']].text)
                            
                            if col_map['vendas'] >= 0:
                                try:
                                    row_data['vendas'] = int(cells[col_map['vendas']].text.strip())
                                except:
                                    row_data['vendas'] = 0
                            
                            if col_map['titulos'] >= 0:
                                row_data['qtd_titulos'] = self.parse_quantity(cells[col_map['titulos']].text)
                            
                            if col_map['total'] >= 0:
                                row_data['total'] = self.parse_money(cells[col_map['total']].text)
                            
                            if row_data.get('data'):
                                report_data['dados_tabela'].append(row_data)
                    
                    # Processa footer para recusadas
                    try:
                        tfoot = table.find_element(By.TAG_NAME, "tfoot")
                        footer_text = tfoot.text
                        recusadas_match = re.search(r'recusadas:\s*(\d+)', footer_text, re.IGNORECASE)
                        if recusadas_match:
                            report_data['resumo']['recusadas'] = int(recusadas_match.group(1))
                    except:
                        pass
                    
                    break
            
            # Calcula resumo
            if report_data['dados_tabela']:
                vendas_total = sum(r.get('vendas', 0) for r in report_data['dados_tabela'])
                titulos_total = sum(r.get('qtd_titulos', 0) for r in report_data['dados_tabela'])
                arrecadado_total = sum(r.get('total', 0) for r in report_data['dados_tabela'])
                
                report_data['resumo'] = {
                    'vendas_total': vendas_total,
                    'titulos_total': titulos_total,
                    'arrecadado_total': arrecadado_total,
                    'dias_com_vendas': len(report_data['dados_tabela']),
                    'ticket_medio_geral': arrecadado_total / titulos_total if titulos_total > 0 else 0,
                    'recusadas': report_data['resumo'].get('recusadas', 0)
                }
                
                self.log(f"      📊 Resumo: {vendas_total} vendas | {titulos_total} títulos | R$ {arrecadado_total:,.2f}")
            else:
                self.log("      ⚠️ Nenhum dado encontrado na tabela")
            
            return report_data
            
        except Exception as e:
            self.log(f"      ❌ Erro ao capturar relatório: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def capture_all_reports(self):
        """Captura relatórios detalhados de todas as rifas"""
        if not self.rifas_data:
            self.log("⚠️ Nenhuma rifa para processar")
            return
        
        self.log(f"\n📈 ETAPA 2: Capturando relatórios detalhados de {len(self.rifas_data)} rifas...")
        self.log("=" * 60)
        
        for i, rifa in enumerate(self.rifas_data):
            self.log(f"\n[{i+1}/{len(self.rifas_data)}] Processando rifa: {rifa.get('titulo', 'Sem título')} (Token: {rifa['data_token'][:20]}...)")
            
            report = self.capture_detailed_report(rifa)
            
            if report:
                # Adiciona o relatório ao dicionário
                token = rifa['data_token']
                self.detailed_reports[token] = report
                
                # Atualiza informações da rifa com dados do relatório
                if report.get('titulo') and not rifa.get('titulo'):
                    rifa['titulo'] = report['titulo']
                
                if 'resumo' in report:
                    rifa['vendas_total'] = report['resumo']['vendas_total']
                    rifa['titulos_total'] = report['resumo']['titulos_total']
                    rifa['arrecadado_total'] = report['resumo']['arrecadado_total']
                    rifa['ticket_medio'] = report['resumo']['ticket_medio_geral']
                    rifa['recusadas'] = report['resumo'].get('recusadas', 0)
            
            # Pequena pausa entre requisições
            time.sleep(self.config.get('capture', {}).get('wait_between_actions', 2))
    
    def save_data(self):
        """Salva todos os dados capturados"""
        timestamp = datetime.now()
        
        # Calcula resumo geral
        resumo = {
            'total_rifas': len(self.rifas_data),
            'rifas_ativas': len([r for r in self.rifas_data if r.get('status') == 'Ativo']),
            'rifas_finalizadas': len([r for r in self.rifas_data if r.get('status') in ['Finalizado', 'Concluído']]),
            'vendas_total': sum(r.get('vendas_total', 0) for r in self.rifas_data),
            'titulos_total': sum(r.get('titulos_total', 0) for r in self.rifas_data),
            'arrecadado_total': sum(r.get('arrecadado_total', 0) for r in self.rifas_data),
            'ticket_medio_geral': 0.0,
            'total_recusadas': sum(r.get('recusadas', 0) for r in self.rifas_data)
        }
        
        if resumo['titulos_total'] > 0:
            resumo['ticket_medio_geral'] = resumo['arrecadado_total'] / resumo['titulos_total']
        
        # Estrutura completa
        data = {
            'captura': {
                'timestamp': timestamp.isoformat(),
                'timestamp_unix': timestamp.timestamp(),
                'data': timestamp.strftime('%Y-%m-%d'),
                'hora': timestamp.strftime('%H:%M:%S'),
                'versao': 'corrected_1.0'
            },
            'resumo_geral': resumo,
            'rifas': self.rifas_data,
            'relatorios_detalhados': self.detailed_reports
        }
        
        # Salva arquivo principal
        filename = f"captura_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.data_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self.log(f"\n💾 Dados salvos em: {filepath}")
        
        # Salva resumo simplificado
        summary_filename = f"resumo_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        summary_filepath = self.data_dir / summary_filename
        
        summary_data = {
            'timestamp': timestamp.isoformat(),
            'resumo': resumo,
            'top_rifas': sorted(
                [r for r in self.rifas_data if r.get('arrecadado_total', 0) > 0],
                key=lambda x: x.get('arrecadado_total', 0),
                reverse=True
            )[:10]
        }
        
        with open(summary_filepath, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)
        
        self.log(f"📊 Resumo salvo em: {summary_filepath}")
        
        return filepath
    
    def display_summary(self):
        """Exibe resumo dos dados capturados"""
        print("\n" + "="*80)
        print("📊 RESUMO DA CAPTURA")
        print("="*80)
        
        resumo = self.rifas_data[0] if len(self.rifas_data) == 1 else {
            'total_rifas': len(self.rifas_data),
            'rifas_ativas': len([r for r in self.rifas_data if r.get('status') == 'Ativo']),
            'vendas_total': sum(r.get('vendas_total', 0) for r in self.rifas_data),
            'titulos_total': sum(r.get('titulos_total', 0) for r in self.rifas_data),
            'arrecadado_total': sum(r.get('arrecadado_total', 0) for r in self.rifas_data),
            'ticket_medio_geral': 0
        }
        
        if isinstance(resumo, dict) and 'total_rifas' in resumo:
            print(f"\n📈 ESTATÍSTICAS GERAIS:")
            print(f"   Total de rifas: {resumo['total_rifas']}")
            print(f"   Rifas ativas: {resumo.get('rifas_ativas', 0)}")
            print(f"   Total de vendas: {resumo.get('vendas_total', 0):,}")
            print(f"   Total de títulos: {resumo.get('titulos_total', 0):,}")
            print(f"   Arrecadação total: R$ {resumo.get('arrecadado_total', 0):,.2f}")
            
            if resumo.get('titulos_total', 0) > 0:
                ticket_medio = resumo.get('arrecadado_total', 0) / resumo.get('titulos_total', 1)
                print(f"   Ticket médio geral: R$ {ticket_medio:.2f}")
        
        # Top 5 rifas
        rifas_com_valor = [r for r in self.rifas_data if r.get('arrecadado_total', 0) > 0]
        if rifas_com_valor:
            print(f"\n🏆 TOP 5 RIFAS POR ARRECADAÇÃO:")
            sorted_rifas = sorted(rifas_com_valor, key=lambda x: x.get('arrecadado_total', 0), reverse=True)[:5]
            
            for i, rifa in enumerate(sorted_rifas, 1):
                print(f"\n   {i}. {rifa.get('titulo', 'Sem título')}")
                print(f"      ID: {rifa.get('id', 'N/A')}")
                print(f"      Arrecadado: R$ {rifa.get('arrecadado_total', 0):,.2f}")
                print(f"      Vendas: {rifa.get('vendas_total', 0):,}")
                print(f"      Status: {rifa.get('status', 'Desconhecido')}")
    
    def run(self, headless=False, capture_details=True):
        """Executa captura completa"""
        print("\n🎰 SISTEMA DE CAPTURA CORRIGIDO - IMPÉRIO RAPIDINHAS")
        print("="*80)
        print("📌 Fluxo correto:")
        print("   1️⃣ Captura lista de rifas com checkboxes e data-tokens")
        print("   2️⃣ Usa data-tokens para acessar relatórios detalhados")
        print("="*80)
        
        try:
            # Setup
            self.setup_driver(headless)
            
            # Login
            if not self.login():
                raise Exception("Falha no login")
            
            # ETAPA 1: Captura lista de rifas
            rifas = self.capture_rifas_list()
            
            if not rifas:
                self.log("\n⚠️ Nenhuma rifa foi capturada!")
                self.log("\n💡 Possíveis causas:")
                self.log("   1. Não há rifas cadastradas")
                self.log("   2. A estrutura da página mudou")
                self.log("   3. Problema de permissão de acesso")
                return None
            
            # ETAPA 2: Captura relatórios detalhados
            if capture_details:
                self.capture_all_reports()
            else:
                self.log("\n⚠️ Captura de detalhes desativada")
            
            # Salva resultados
            filepath = self.save_data()
            
            # Exibe resumo
            self.display_summary()
            
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
    capture = ImperioCapturaCorrected()
    
    # Verifica argumentos
    headless = '--headless' in sys.argv
    no_details = '--no-details' in sys.argv
    
    capture.run(headless=headless, capture_details=not no_details)
    
    if not headless:
        input("\nPressione ENTER para fechar...")

if __name__ == "__main__":
    main()