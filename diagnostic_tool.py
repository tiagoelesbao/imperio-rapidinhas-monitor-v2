#!/usr/bin/env python3
"""
Ferramenta de Diagnóstico - Império Rapidinhas
Identifica a estrutura real da página para debug
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoAlertPresentException
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
from pathlib import Path

class ImperioDiagnostic:
    def __init__(self, config_file='./config/config.json'):
        """Inicializa diagnóstico"""
        self.config = self.load_config(config_file)
        self.driver = None
        
    def load_config(self, config_file):
        """Carrega configuração"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            print("❌ Erro ao carregar configuração!")
            exit(1)
    
    def setup_driver(self):
        """Configura driver"""
        print("🔧 Configurando navegador para diagnóstico...")
        
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        print("✅ Navegador configurado!")
    
    def handle_alert(self):
        """Trata alerts"""
        try:
            alert = self.driver.switch_to.alert
            print(f"📢 Alert detectado: '{alert.text}'")
            alert.accept()
            time.sleep(1)
        except NoAlertPresentException:
            pass
    
    def login(self):
        """Faz login"""
        print("\n🔐 Fazendo login...")
        
        self.driver.get(f"{self.config['imperio']['base_url']}/auth")
        time.sleep(2)
        
        # Login
        username_field = self.driver.find_element(By.NAME, "username")
        password_field = self.driver.find_element(By.NAME, "password")
        
        username_field.send_keys(self.config['imperio']['username'])
        password_field.send_keys(self.config['imperio']['password'])
        
        login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        
        time.sleep(3)
        self.handle_alert()
        
        print("✅ Login realizado!")
    
    def diagnose_rifas_page(self):
        """Diagnostica página de rifas"""
        print("\n🔍 DIAGNÓSTICO DA PÁGINA DE RIFAS")
        print("="*60)
        
        # Navega para rifas
        self.driver.get(f"{self.config['imperio']['base_url']}/admin/rifas")
        time.sleep(3)
        self.handle_alert()
        
        # Salva screenshot
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot_file = f"diagnostic_screenshot_{timestamp}.png"
        self.driver.save_screenshot(screenshot_file)
        print(f"📸 Screenshot salvo: {screenshot_file}")
        
        # Salva HTML
        html_file = f"diagnostic_html_{timestamp}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(self.driver.page_source)
        print(f"📄 HTML salvo: {html_file}")
        
        # Analisa estrutura
        print("\n📊 ANÁLISE DA ESTRUTURA:")
        
        # 1. Checkboxes
        print("\n1️⃣ CHECKBOXES:")
        checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
        print(f"   Total de checkboxes na página: {len(checkboxes)}")
        
        for i, cb in enumerate(checkboxes[:5]):  # Primeiros 5
            print(f"\n   Checkbox {i+1}:")
            print(f"      Name: {cb.get_attribute('name')}")
            print(f"      Value: {cb.get_attribute('value')}")
            print(f"      ID: {cb.get_attribute('id')}")
            print(f"      Class: {cb.get_attribute('class')}")
            print(f"      Data-token: {cb.get_attribute('data-token')}")
        
        # 2. Tabelas
        print("\n2️⃣ TABELAS:")
        tables = self.driver.find_elements(By.TAG_NAME, "table")
        print(f"   Total de tabelas: {len(tables)}")
        
        for i, table in enumerate(tables):
            print(f"\n   Tabela {i+1}:")
            print(f"      Class: {table.get_attribute('class')}")
            print(f"      ID: {table.get_attribute('id')}")
            
            # Headers
            headers = table.find_elements(By.CSS_SELECTOR, "thead th")
            if headers:
                print(f"      Headers: {[h.text for h in headers]}")
            
            # Linhas
            rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
            print(f"      Total de linhas: {len(rows)}")
        
        # 3. Links com "rifa"
        print("\n3️⃣ LINKS RELACIONADOS:")
        links = self.driver.find_elements(By.TAG_NAME, "a")
        rifa_links = [l for l in links if 'rifa' in l.get_attribute('href', '').lower()]
        print(f"   Links com 'rifa': {len(rifa_links)}")
        
        for link in rifa_links[:5]:
            print(f"      {link.get_attribute('href')}")
        
        # 4. Elementos com data-token
        print("\n4️⃣ ELEMENTOS COM DATA-TOKEN:")
        script = """
        return Array.from(document.querySelectorAll('[data-token]')).map(el => ({
            tag: el.tagName,
            type: el.type || '',
            dataToken: el.getAttribute('data-token'),
            text: el.textContent.trim().substring(0, 50)
        }));
        """
        elements_with_token = self.driver.execute_script(script)
        print(f"   Total: {len(elements_with_token)}")
        
        for elem in elements_with_token[:5]:
            print(f"      {elem}")
        
        # 5. Estrutura geral
        print("\n5️⃣ ESTRUTURA GERAL DA PÁGINA:")
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        
        # Busca elementos chave
        form_rifas = soup.find('form', {'name': 'form_rifas'})
        if form_rifas:
            print("   ✅ Formulário 'form_rifas' encontrado")
        
        # Busca containers principais
        main_containers = soup.find_all(['div', 'section'], class_=lambda x: x and ('container' in x or 'content' in x))
        print(f"   Containers principais: {len(main_containers)}")
        
        # 6. Busca específica por padrões de rifa
        print("\n6️⃣ PADRÕES DE RIFA ENCONTRADOS:")
        
        # Busca por texto
        text_patterns = [
            r'#\d{4,}',  # IDs como #1234
            r'\d+º?\s*RAPIDINHA',  # Títulos
            r'R\$\s*[\d.,]+',  # Valores
        ]
        
        body_text = soup.get_text()
        for pattern in text_patterns:
            import re
            matches = re.findall(pattern, body_text)[:5]
            if matches:
                print(f"   Padrão '{pattern}': {matches}")
        
        # Salva resultado do diagnóstico
        result = {
            'timestamp': datetime.now().isoformat(),
            'url': self.driver.current_url,
            'title': self.driver.title,
            'checkboxes_found': len(checkboxes),
            'tables_found': len(tables),
            'elements_with_token': len(elements_with_token),
            'screenshot': screenshot_file,
            'html_file': html_file
        }
        
        result_file = f"diagnostic_result_{timestamp}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n💾 Resultado salvo em: {result_file}")
        
        return result
    
    def test_direct_api_access(self):
        """Testa acesso direto a relatórios"""
        print("\n🔬 TESTE DE ACESSO DIRETO A RELATÓRIOS")
        print("="*60)
        
        # Tenta encontrar tokens de exemplo
        checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[data-token]")
        
        if checkboxes:
            test_token = checkboxes[0].get_attribute('data-token')
            test_url = f"{self.config['imperio']['base_url']}/admin/rifas/relatorios/{test_token}"
            
            print(f"🔗 Testando URL: {test_url}")
            self.driver.get(test_url)
            time.sleep(2)
            
            # Verifica se carregou
            if "relatorio" in self.driver.current_url.lower():
                print("✅ Acesso ao relatório funcionou!")
                
                # Analisa estrutura do relatório
                tables = self.driver.find_elements(By.TAG_NAME, "table")
                print(f"   Tabelas no relatório: {len(tables)}")
                
                for table in tables:
                    headers = table.find_elements(By.CSS_SELECTOR, "thead th")
                    if headers:
                        print(f"   Headers: {[h.text for h in headers]}")
            else:
                print("❌ Não foi possível acessar o relatório")
        else:
            print("⚠️ Nenhum token encontrado para teste")
    
    def run(self):
        """Executa diagnóstico completo"""
        print("🏥 FERRAMENTA DE DIAGNÓSTICO - IMPÉRIO RAPIDINHAS")
        print("="*60)
        
        try:
            self.setup_driver()
            self.login()
            
            # Diagnóstico principal
            result = self.diagnose_rifas_page()
            
            # Teste adicional
            self.test_direct_api_access()
            
            print("\n✅ Diagnóstico concluído!")
            print("\n📋 RESUMO:")
            print(f"   - Screenshot: {result['screenshot']}")
            print(f"   - HTML: {result['html_file']}")
            print(f"   - Resultado: {result_file}")
            print("\n💡 Analise estes arquivos para entender a estrutura da página")
            
        except Exception as e:
            print(f"\n❌ Erro no diagnóstico: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            if self.driver:
                input("\n\nPressione ENTER para fechar o navegador...")
                self.driver.quit()

def main():
    diagnostic = ImperioDiagnostic()
    diagnostic.run()

if __name__ == "__main__":
    main()