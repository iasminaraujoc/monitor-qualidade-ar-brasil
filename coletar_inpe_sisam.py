from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import pandas as pd
import json
import time
import os
from datetime import datetime
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class ColetorINPESelenium:
    """
    Coletor INPE SISAM usando Selenium - Dados de Hoje + Semana Epidemiológica
    """
    
    def __init__(self, headless=True, pasta_download=None):
        self.base_url = "https://data.inpe.br/queimadas/sisam"
        
        # Configurar pasta de download
        if pasta_download is None:
            pasta_download = os.path.join(os.getcwd(), 'downloads_inpe')
        
        os.makedirs(pasta_download, exist_ok=True)
        self.pasta_download = pasta_download
        
        # Configurar Chrome
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Configurar pasta de download
        prefs = {
            'download.default_directory': pasta_download,
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'safebrowsing.enabled': True
        }
        chrome_options.add_experimental_option('prefs', prefs)
        
        # Usar webdriver-manager para baixar automaticamente
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        
        self.estados = {
            'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas',
            'BA': 'Bahia', 'CE': 'Ceará', 'DF': 'Distrito Federal',
            'ES': 'Espírito Santo', 'GO': 'Goiás', 'MA': 'Maranhão',
            'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul', 'MG': 'Minas Gerais',
            'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná', 'PE': 'Pernambuco',
            'PI': 'Piauí', 'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte',
            'RS': 'Rio Grande do Sul', 'RO': 'Rondônia', 'RR': 'Roraima',
            'SC': 'Santa Catarina', 'SP': 'São Paulo', 'SE': 'Sergipe',
            'TO': 'Tocantins'
        }
    
    def obter_dados_hoje_estado(self, estado_sigla):
        """
        Obtém dados de hoje para um estado específico
        """
        url = f"{self.base_url}/"
        
        try:
            print(f"   {estado_sigla}...", end=" ", flush=True)
            self.driver.get(url)
            
            # Aguardar carregamento da página
            time.sleep(3)
            
            # Procurar e selecionar o estado no dropdown
            try:
                select_element = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "select, #estado-select, [name='estado']"))
                )
                select = Select(select_element)
                select.select_by_value(estado_sigla)
                
                # Aguardar dados carregarem
                time.sleep(3)
            except:
                # Se não encontrar dropdown, tentar outro método
                pass
            
            # Extrair indicadores ambientais
            indicadores = {}
            
            try:
                # Tentar diferentes seletores
                cards = self.driver.find_elements(By.CSS_SELECTOR, 
                    ".indicator, .metric, .card, [class*='poluente'], [class*='indicador']")
                
                for card in cards:
                    texto = card.text
                    if any(pol in texto.upper() for pol in ['PM2.5', 'PM10', 'PM₂.₅', 'PM₁₀', 'SO2', 'NO2', 'O3', 'CO']):
                        indicadores[texto] = card.text
                
                # Se não encontrou nada, tentar pegar todo o texto visível
                if not indicadores:
                    body = self.driver.find_element(By.TAG_NAME, "body")
                    texto_completo = body.text
                    
                    # Procurar por padrões de dados
                    import re
                    padroes = {
                        'PM2.5': r'PM[₂2]\.?5[^\d]*(\d+\.?\d*)',
                        'PM10': r'PM[₁1]0[^\d]*(\d+\.?\d*)',
                        'SO2': r'SO[₂2][^\d]*(\d+\.?\d*)',
                        'NO2': r'NO[₂2][^\d]*(\d+\.?\d*)',
                        'O3': r'O[₃3][^\d]*(\d+\.?\d*)',
                        'CO': r'CO[^\d]*(\d+\.?\d*)',
                    }
                    
                    for poluente, padrao in padroes.items():
                        match = re.search(padrao, texto_completo, re.IGNORECASE)
                        if match:
                            indicadores[poluente] = float(match.group(1))
            
            except Exception as e:
                print(f"⚠️ Erro ao extrair: {e}")
            
            print("✅" if indicadores else "⚠️")
            
            return {
                'estado': estado_sigla,
                'estado_nome': self.estados[estado_sigla],
                'data_coleta': datetime.now().isoformat(),
                'indicadores': indicadores
            }
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            return None
    
    def baixar_semana_epidemiologica_municipios(self):
        """
        Baixa dados de semana epidemiológica (últimas 5 semanas) de todos os municípios
        """
        print("=" * 60)
        print("📊 BAIXANDO SEMANA EPIDEMIOLÓGICA - MUNICÍPIOS")
        print("=" * 60)
        print("📅 Período: Últimas 5 semanas")
        print(f"📁 Pasta de download: {self.pasta_download}")
        print()
        
        # Acessar página de histórico (qualquer estado serve para acessar o modal)
        url = f"{self.base_url}/historico"
        
        try:
            print("🔍 Acessando página de histórico...")
            self.driver.get(url)
            time.sleep(5)
            
            # Procurar pelo botão/link que abre o modal de Semana Epidemiológica
            print("🔍 Procurando botão 'Área de Download'...")
            
            try:
                botao_area = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Área de Download')]")
                print(f"✅ Botão 'Área de Download' encontrado")
                botao_area.click()
                time.sleep(3)
            except:
                print("⚠️ Botão não encontrado, modal pode já estar aberto")
            
            # Procurar pelo radio button de "Municípios - Todas as 5 semanas"
            print("🔍 Selecionando opção de municípios (últimas 5 semanas)...")
            
            try:
                # Tentar encontrar o radio button pelo value
                radio = self.driver.find_element(By.XPATH, 
                    "//input[@value='semana_epidemiologica_municipio_todas_5_semanas']")
                print(f"✅ Radio button encontrado")
                
                # Clicar usando JavaScript para garantir que funcione
                self.driver.execute_script("arguments[0].click();", radio)
                time.sleep(2)
                print("✅ Opção selecionada")
            except Exception as e:
                print(f"⚠️ Erro ao selecionar radio: {e}")
                print("⚠️ Tentando continuar mesmo assim...")
            
            # Procurar e clicar no botão de download usando a classe específica
            print("🔍 Procurando botão de download...")
            
            try:
                # Método 1: Encontrar pelo class name
                btn_download = self.driver.find_element(By.CLASS_NAME, "btn-download")
                print(f"✅ Botão de download encontrado (classe btn-download)")
                
                # Rolar até o botão para garantir que está visível
                self.driver.execute_script("arguments[0].scrollIntoView(true);", btn_download)
                time.sleep(1)
                
                # Verificar quantos arquivos existem antes do download
                arquivos_antes = set(os.listdir(self.pasta_download))
                
                # Tentar clicar de várias formas
                print("📥 Tentando clicar no botão...")
                
                # Forma 1: Clicar usando JavaScript diretamente
                try:
                    self.driver.execute_script("arguments[0].click();", btn_download)
                    print("   Método 1: JavaScript click()")
                    time.sleep(2)
                except:
                    pass
                
                # Forma 2: Executar a função processDownload() diretamente
                try:
                    self.driver.execute_script("processDownload();")
                    print("   Método 2: processDownload()")
                    time.sleep(2)
                except:
                    pass
                
                # Forma 3: Clicar normal
                try:
                    btn_download.click()
                    print("   Método 3: click() normal")
                    time.sleep(2)
                except:
                    pass
                
                print("⏳ Aguardando download (15 segundos)...")
                time.sleep(15)
                
                # Verificar se algum arquivo novo foi baixado
                arquivos_depois = set(os.listdir(self.pasta_download))
                arquivos_novos = arquivos_depois - arquivos_antes
                
                if arquivos_novos:
                    print(f"✅ Download concluído!")
                    print(f"📄 Arquivo(s) baixado(s):")
                    
                    for arquivo in arquivos_novos:
                        caminho_completo = os.path.join(self.pasta_download, arquivo)
                        tamanho = os.path.getsize(caminho_completo)
                        print(f"   • {arquivo} ({tamanho:,} bytes)")
                        
                        # Se for CSV, tentar ler
                        if arquivo.endswith('.csv'):
                            try:
                                df = pd.read_csv(caminho_completo, encoding='utf-8')
                                print(f"\n📊 Dados carregados do arquivo {arquivo}:")
                                print(f"   Linhas: {len(df)}")
                                print(f"   Colunas: {len(df.columns)}")
                                if len(df.columns) > 0:
                                    print(f"   Colunas: {', '.join(df.columns.tolist()[:5])}...")
                                return df
                            except Exception as e:
                                print(f"⚠️ Erro ao ler arquivo: {e}")
                    
                    # Se não conseguiu ler nenhum CSV, retornar o primeiro arquivo
                    primeiro_arquivo = list(arquivos_novos)[0]
                    caminho = os.path.join(self.pasta_download, primeiro_arquivo)
                    try:
                        df = pd.read_csv(caminho)
                        return df
                    except:
                        print(f"⚠️ Não foi possível ler como CSV")
                        return None
                else:
                    print("❌ Nenhum arquivo novo foi baixado")
                    print(f"   Arquivos na pasta antes: {len(arquivos_antes)}")
                    print(f"   Arquivos na pasta depois: {len(arquivos_depois)}")
                    
                    # Tentar ver se há algum erro na página
                    try:
                        body_text = self.driver.find_element(By.TAG_NAME, "body").text
                        if 'erro' in body_text.lower() or 'error' in body_text.lower():
                            print(f"⚠️ Possível erro na página: {body_text[:200]}")
                    except:
                        pass
                    
                    return None
                    
            except Exception as e:
                print(f"❌ Erro ao clicar no botão: {e}")
                import traceback
                traceback.print_exc()
                
                # Tentar executar processDownload() diretamente como último recurso
                print("\n🔄 Última tentativa: executar processDownload() diretamente...")
                try:
                    self.driver.execute_script("processDownload();")
                    time.sleep(15)
                    
                    arquivos = os.listdir(self.pasta_download)
                    arquivos_csv = [f for f in arquivos if f.endswith('.csv')]
                    
                    if arquivos_csv:
                        arquivo_mais_recente = max(
                            [os.path.join(self.pasta_download, f) for f in arquivos_csv],
                            key=os.path.getctime
                        )
                        df = pd.read_csv(arquivo_mais_recente)
                        print(f"✅ Arquivo lido: {os.path.basename(arquivo_mais_recente)}")
                        return df
                except Exception as e2:
                    print(f"❌ Também falhou: {e2}")
                
                return None
                
        except Exception as e:
            print(f"❌ Erro geral: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def coletar_dados_hoje_todos_estados(self):
        """
        Coleta dados de hoje de todos os estados
        """
        print("=" * 60)
        print("📊 COLETANDO DADOS DE HOJE - TODOS OS ESTADOS")
        print("=" * 60)
        print(f"🕐 Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🗺️  Estados: {len(self.estados)}")
        print()
        
        todos_dados = []
        
        for i, sigla in enumerate(self.estados.keys(), 1):
            print(f"[{i}/{len(self.estados)}] ", end="")
            dados = self.obter_dados_hoje_estado(sigla)
            if dados:
                todos_dados.append(dados)
            time.sleep(1)
        
        return pd.DataFrame(todos_dados)
    
    def fechar(self):
        """
        Fecha o navegador
        """
        self.driver.quit()
    
    def executar_coleta_completa(self):
        """
        Executa coleta completa: dados de hoje + semana epidemiológica
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 1. Coletar dados de hoje
            # print("\n" + "=" * 60)
            # print("1️⃣ COLETA DE DADOS DE HOJE")
            # print("=" * 60)
            
            # dados_hoje = self.coletar_dados_hoje_todos_estados()
            
            # if len(dados_hoje) > 0:
            #     arquivo_csv = f'dados_inpe_hoje_{timestamp}.csv'
            #     dados_hoje.to_csv(arquivo_csv, index=False, encoding='utf-8')
                
            #     arquivo_json = f'dados_inpe_hoje_{timestamp}.json'
            #     dados_hoje.to_json(arquivo_json, orient='records', indent=2, force_ascii=False)
                
            #     print(f"\n💾 Dados de hoje salvos:")
            #     print(f"   • {arquivo_csv}")
            #     print(f"   • {arquivo_json}")
            
            # 2. Baixar semana epidemiológica dos municípios
            print("\n" + "=" * 60)
            print("2️⃣ DOWNLOAD SEMANA EPIDEMIOLÓGICA - MUNICÍPIOS")
            print("=" * 60)
            
            dados_semana = self.baixar_semana_epidemiologica_municipios()
            
            if dados_semana is not None and len(dados_semana) > 0:
                arquivo_semana = f'dados_inpe_semana_epidemiologica_municipios_{timestamp}.csv'
                dados_semana.to_csv(arquivo_semana, index=False, encoding='utf-8')
                print(f"\n💾 Dados de semana epidemiológica salvos:")
                print(f"   • {arquivo_semana}")
            
            # Resumo final
            print("\n" + "=" * 60)
            print("✅ COLETA CONCLUÍDA!")
            print("=" * 60)
            print(f"🕐 Término: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"📊 Dados de hoje: {len(dados_hoje)} estados")
            if dados_semana is not None:
                print(f"📊 Semana epidemiológica: {len(dados_semana)} registros")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Erro durante a coleta: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("\n🔒 Fechando navegador...")
            self.fechar()


if __name__ == "__main__":
    print("=" * 60)
    print("🌐 COLETOR INPE SISAM")
    print("=" * 60)
    print("📊 Funcionalidades:")
    print("   1. Dados de hoje (todos os estados)")
    print("   2. Semana epidemiológica (municípios - 5 semanas)")
    print("=" * 60)
    print()
    
    # Criar coletor e executar
    coletor = ColetorINPESelenium(headless=True)
    coletor.executar_coleta_completa()