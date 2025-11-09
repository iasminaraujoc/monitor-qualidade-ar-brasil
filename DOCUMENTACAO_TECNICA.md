# Documentação Técnica - Monitor de Qualidade do Ar - Brasil

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Módulo de Coleta de Dados (Scraping)](#módulo-de-coleta-de-dados-scraping)
4. [Módulo de Dashboard](#módulo-de-dashboard)
5. [Fluxo de Dados](#fluxo-de-dados)
6. [Relações entre Funções](#relações-entre-funções)
7. [Estrutura de Dados](#estrutura-de-dados)

---

## Visão Geral

Este sistema é composto por dois módulos principais que trabalham em conjunto para coletar, processar e visualizar dados de qualidade do ar do Brasil através do sistema INPE SISAM (Sistema de Informações Ambientais Integrado à Saúde).

### Componentes Principais

- **`coletar_inpe_sisam.py`**: Módulo responsável pela coleta automatizada de dados via web scraping usando Selenium
- **`dashboard_qualidade_ar.py`**: Aplicação Streamlit que processa e visualiza os dados coletados

### Tecnologias Utilizadas

- **Selenium WebDriver**: Automação de navegador para scraping
- **Streamlit**: Framework para criação de dashboards interativos
- **Pandas**: Manipulação e processamento de dados
- **Plotly**: Visualizações interativas de gráficos
- **Firefox/GeckoDriver**: Navegador automatizado para coleta

---

## Arquitetura do Sistema

### Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    INPE SISAM (Fonte)                       │
│              https://data.inpe.br/queimadas/sisam           │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ HTTP Requests (Selenium)
                        ▼
┌─────────────────────────────────────────────────────────────┐
│         coletar_inpe_sisam.py (Módulo de Coleta)           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ColetorINPESelenium                                  │  │
│  │  - baixar_semana_epidemiologica_municipios()         │  │
│  │  - coletar_dados_hoje_todos_estados()                │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ Salva arquivos CSV
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              downloads_inpe/ (Armazenamento)                │
│  - dados_inpe_hoje_YYYYMMDD_HHMMSS.csv                     │
│  - dados_inpe_semana_epidemiologica_municipios_*.csv       │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ Lê arquivos mais recentes
                        ▼
┌─────────────────────────────────────────────────────────────┐
│        dashboard_qualidade_ar.py (Módulo de Visualização)  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Funções de Processamento                            │  │
│  │  - carregar_dados()                                  │  │
│  │  - processar_dados_semana()                         │  │
│  │  - calcular_aqi_pm25()                              │  │
│  │  - obter_categoria_aqi()                            │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Funções de Visualização                              │  │
│  │  - main() (orquestra todas as tabs)                  │  │
│  │  - Tabs: Visão Geral, Série Temporal, Rankings, etc │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ Renderiza interface web
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Dashboard Interativo (Streamlit)                │
│  - Visualizações gráficas (Plotly)                          │
│  - Filtros interativos                                      │
│  - Métricas e estatísticas                                  │
└─────────────────────────────────────────────────────────────┘
```

### Padrão de Arquitetura

O sistema segue um padrão **ETL (Extract, Transform, Load)** simplificado:

1. **Extract (Extração)**: O módulo `coletar_inpe_sisam.py` extrai dados do site do INPE
2. **Transform (Transformação)**: Os dados são salvos em CSV e depois processados pelo dashboard
3. **Load (Carregamento)**: O dashboard carrega, processa e exibe os dados

---

## Módulo de Coleta de Dados (Scraping)

### Classe: `ColetorINPESelenium`

Esta classe encapsula toda a lógica de automação web para coletar dados do INPE SISAM.

#### Inicialização (`__init__`)

```python
def __init__(self, headless=True, pasta_download=None)
```

**Funcionalidades:**
- Configura o navegador Firefox com Selenium WebDriver
- Define a pasta de download padrão (`downloads_inpe/`)
- Configura opções do navegador (headless, user-agent, etc.)
- Inicializa o WebDriverWait para aguardar elementos da página
- Define mapeamento de estados brasileiros (sigla → nome completo)

**Parâmetros:**
- `headless`: Se `True`, executa o navegador em modo invisível
- `pasta_download`: Caminho onde os arquivos CSV serão salvos

#### Método: `baixar_semana_epidemiologica_municipios()`

**Propósito**: Baixa dados históricos de semana epidemiológica (últimas 5 semanas) de todos os municípios brasileiros.

**Fluxo de Execução:**

1. **Acesso à Página de Histórico**
   ```python
   url = f"{self.base_url}/historico"
   self.driver.get(url)
   ```
   - Navega para a página de histórico do INPE SISAM
   - Aguarda 5 segundos para carregamento completo

2. **Localização do Botão de Download**
   - Procura pelo elemento com texto "Área de Download"
   - Clica no botão para abrir o modal de download
   - Utiliza XPath para localização: `//*[contains(text(), 'Área de Download')]`

3. **Seleção da Opção de Dados**
   - Localiza o radio button com valor `semana_epidemiologica_municipio_todas_5_semanas`
   - Clica usando JavaScript para garantir execução: `driver.execute_script("arguments[0].click();", radio)`
   - Esta opção seleciona dados de todos os municípios das últimas 5 semanas epidemiológicas

4. **Trigger do Download**
   - Localiza o botão de download pela classe `btn-download`
   - Tenta múltiplos métodos de clique para garantir sucesso:
     - Método 1: Clique via JavaScript
     - Método 2: Execução direta da função `processDownload()`
     - Método 3: Clique normal do Selenium
   - Aguarda 15 segundos para conclusão do download

5. **Verificação do Arquivo Baixado**
   - Compara lista de arquivos antes e depois do download
   - Identifica novos arquivos na pasta de download
   - Valida se o arquivo é CSV e tenta carregá-lo com Pandas
   - Retorna DataFrame com os dados ou `None` em caso de falha

**Tratamento de Erros:**
- Múltiplas tentativas de clique no botão
- Fallback para execução direta de JavaScript
- Validação de arquivos baixados
- Logs detalhados de cada etapa

#### Método: `obter_dados_hoje_estado(estado_sigla)`

**Propósito**: Coleta dados atuais de qualidade do ar para um estado específico.

**Fluxo:**
1. Navega para a página principal do SISAM
2. Localiza e seleciona o estado no dropdown
3. Extrai indicadores ambientais (PM2.5, PM10, O3, etc.) da página
4. Utiliza múltiplos seletores CSS para encontrar elementos
5. Se não encontrar elementos estruturados, usa regex para extrair valores do texto da página

**Retorno:**
```python
{
    'estado': 'SP',
    'estado_nome': 'São Paulo',
    'data_coleta': '2025-11-08T17:53:56',
    'indicadores': {'PM2.5': 12.5, 'PM10': 25.3, ...}
}
```

#### Método: `executar_coleta_completa()`

**Propósito**: Orquestra todo o processo de coleta.

**Fluxo:**
1. Gera timestamp para nomeação de arquivos
2. Executa `baixar_semana_epidemiologica_municipios()`
3. Salva o DataFrame retornado em CSV com timestamp
4. Fecha o navegador ao finalizar

**Nota**: A coleta de dados de hoje está comentada no código atual, focando apenas na semana epidemiológica.

---

## Módulo de Dashboard

### Estrutura Geral

O dashboard é uma aplicação Streamlit organizada em múltiplas abas (tabs) que apresentam diferentes visualizações dos dados.

### Funções de Processamento

#### `carregar_dados()` (com cache)

```python
@st.cache_data(ttl=300)
def carregar_dados()
```

**Propósito**: Carrega os arquivos CSV mais recentes da pasta `downloads_inpe/`.

**Funcionalidades:**
- Utiliza `glob` para encontrar arquivos que seguem padrões específicos:
  - `dados_inpe_semana_*.csv` para dados de semana epidemiológica
  - `dados_inpe_hoje_*.csv` para dados do dia atual
- Identifica o arquivo mais recente usando `os.path.getctime()`
- Carrega os CSVs com `pd.read_csv()`
- Retorna dicionário com DataFrames e nomes dos arquivos

**Cache**: Utiliza `@st.cache_data(ttl=300)` para cachear resultados por 5 minutos, evitando recarregar dados desnecessariamente.

**Retorno:**
```python
{
    'semana': DataFrame,
    'arquivo_semana': 'dados_inpe_semana_...csv',
    'hoje': DataFrame,
    'arquivo_hoje': 'dados_inpe_hoje_...csv'
}
```

#### `processar_dados_semana(df)`

**Propósito**: Normaliza e enriquece o DataFrame de semana epidemiológica.

**Transformações Realizadas:**

1. **Conversão de Datas**
   ```python
   df['data'] = pd.to_datetime(df['date'], errors='coerce')
   ```
   - Converte coluna `date` para tipo datetime
   - `errors='coerce'` transforma valores inválidos em NaT

2. **Renomeação de Colunas**
   - Padroniza nomes longos do INPE para nomes curtos:
     - `pm2_5_media_diaria_previsao_situacao_atual` → `PM2.5`
     - `pm10_media_diaria_previsao_situacao_atual` → `PM10`
     - `o3_media_diaria_previsao_situacao_atual` → `O3`

3. **Cálculo de AQI (Air Quality Index)**
   ```python
   df['AQI'] = df['PM2.5'].apply(calcular_aqi_pm25)
   ```
   - Aplica função `calcular_aqi_pm25()` para cada valor de PM2.5
   - Cria coluna `AQI` com índice de qualidade do ar

4. **Categorização**
   ```python
   df['Categoria'] = df['AQI'].apply(lambda x: obter_categoria_aqi(x)[0])
   df['Cor'] = df['AQI'].apply(lambda x: obter_categoria_aqi(x)[1])
   ```
   - Classifica cada registro em categorias (Boa, Moderada, Insalubre, etc.)
   - Atribui cores correspondentes para visualização

**Retorno**: DataFrame processado com colunas adicionais (`data`, `PM2.5`, `PM10`, `O3`, `AQI`, `Categoria`, `Cor`)

#### `calcular_aqi_pm25(concentracao)`

**Propósito**: Calcula o Air Quality Index (AQI) baseado na concentração de PM2.5.

**Algoritmo:**
Utiliza fórmula de interpolação linear baseada nos breakpoints do EPA (Environmental Protection Agency):

```
Se concentracao <= 12:
    AQI = (concentracao / 12) * 50
Se 12 < concentracao <= 35.4:
    AQI = 50 + ((concentracao - 12) / 23.4) * 50
Se 35.4 < concentracao <= 55.4:
    AQI = 100 + ((concentracao - 35.4) / 20) * 50
... e assim por diante
```

**Categorias AQI:**
- 0-50: Boa (verde)
- 51-100: Moderada (amarelo)
- 101-150: Insalubre para Sensíveis (laranja)
- 151-200: Insalubre (vermelho)
- 201-300: Muito Insalubre (roxo)
- 301-500: Perigosa (vermelho escuro)

#### `obter_categoria_aqi(aqi)`

**Propósito**: Mapeia valor de AQI para categoria e cor correspondente.

**Lógica:**
- Itera sobre `CATEGORIAS_AQI` (lista de dicionários)
- Retorna nome da categoria e cor hexadecimal quando encontra intervalo correspondente
- Retorna 'Sem dados' e cor cinza para valores NaN

### Função Principal: `main()`

**Propósito**: Orquestra toda a interface do dashboard.

**Estrutura:**

1. **Configuração Inicial**
   - Define título e ícone da página
   - Carrega dados usando `carregar_dados()`

2. **Sidebar (Barra Lateral)**
   - Exibe informações dos arquivos carregados
   - Mostra padrões OMS 2021 como referência

3. **Tabs (Abas Principais)**

   **Tab 1: Visão Geral**
   - **Métricas Principais**: 4 colunas com KPIs
     - Total de municípios
     - PM2.5 médio (com delta vs OMS)
     - PM10 médio (com delta vs OMS)
     - Data da última medição
   
   - **Gráfico de Barras por Estado**
     - Top 15 estados com maior concentração média de PM2.5
     - Linha de referência do limite OMS (15 µg/m³)
     - Utiliza Plotly Express (`px.bar`)
   
   - **Distribuição de Categorias**
     - Gráfico de pizza mostrando proporção de cada categoria AQI
     - Histograma de distribuição de concentrações PM2.5
     - Linhas de referência para limites OMS e crítico
   
   - **Estatísticas Gerais**
     - 3 colunas (PM2.5, PM10, O3)
     - Métricas: acima do limite OMS, percentual, máximo registrado

   **Tab 2: Série Temporal**
   - **Filtros Interativos**
     - Dropdown de estados (com opção "Todos")
     - Dropdown de municípios (dinâmico baseado no estado selecionado)
   
   - **Gráfico de Linha Temporal**
     - 3 séries: PM2.5, PM10, O3
     - Agrupamento por data com média dos valores
     - Linhas de referência horizontais para limites OMS
     - Utiliza Plotly Graph Objects (`go.Figure`)
   
   - **Estatísticas do Período**
     - Mínimo, médio e máximo para cada poluente

   **Tab 3: Rankings**
   - **Seletor de Poluente**: PM2.5, PM10, O3 ou AQI
   - **Top 10 Melhor Qualidade**: Menores valores do poluente selecionado
   - **Top 10 Pior Qualidade**: Maiores valores do poluente selecionado
   - **Gráfico Comparativo**: Barras horizontais comparando melhores vs piores
   - Linha de referência do limite OMS quando aplicável

   **Tab 4: Dados Brutos**
   - **Tabela Interativa**: DataFrame completo com filtros
   - **Filtros Multiselect**: Por estado e por categoria
   - **Botões de Download**: CSV filtrado ou completo

4. **Rodapé**
   - Informações sobre fonte de dados e padrões utilizados

---

## Fluxo de Dados

### Fluxo Completo

```
1. EXECUÇÃO DO COLETOR
   └─> coletar_inpe_sisam.py
       └─> ColetorINPESelenium.executar_coleta_completa()
           └─> baixar_semana_epidemiologica_municipios()
               └─> Selenium interage com site INPE
                   └─> Download automático de CSV
                       └─> Salva em downloads_inpe/dados_inpe_semana_*.csv

2. EXECUÇÃO DO DASHBOARD
   └─> dashboard_qualidade_ar.py
       └─> main()
           └─> carregar_dados() [CACHEADO]
               └─> glob.glob() encontra arquivos mais recentes
                   └─> pd.read_csv() carrega CSVs
                       └─> Retorna dicionário com DataFrames
                           └─> processar_dados_semana()
                               └─> Normaliza colunas
                                   └─> calcular_aqi_pm25() para cada registro
                                       └─> obter_categoria_aqi() para cada AQI
                                           └─> DataFrame processado pronto para visualização
                                               └─> Renderização nas tabs do Streamlit
                                                   └─> Plotly gera gráficos interativos
```

### Fluxo de Processamento de Dados

```
CSV Bruto (INPE)
    │
    ├─> Renomeação de colunas
    │   └─> pm2_5_media_diaria... → PM2.5
    │
    ├─> Conversão de tipos
    │   └─> date → datetime
    │
    ├─> Cálculo de métricas derivadas
    │   ├─> AQI = calcular_aqi_pm25(PM2.5)
    │   └─> Categoria = obter_categoria_aqi(AQI)
    │
    └─> DataFrame Processado
        │
        ├─> Agregações (groupby)
        │   ├─> Por estado: média de PM2.5, PM10, O3
        │   ├─> Por município: média de poluentes
        │   └─> Por data: média temporal
        │
        └─> Visualizações
            ├─> Gráficos de barras (Plotly Express)
            ├─> Gráficos de linha (Plotly Graph Objects)
            ├─> Gráficos de pizza (Plotly Express)
            └─> Histogramas (Plotly Express)
```

---

## Relações entre Funções

### Hierarquia de Chamadas

```
main()
│
├─> carregar_dados()
│   └─> (usa glob, os.path, pd.read_csv)
│
├─> processar_dados_semana(df)
│   ├─> calcular_aqi_pm25(concentracao)
│   └─> obter_categoria_aqi(aqi)
│       └─> (usa CATEGORIAS_AQI)
│
└─> Visualizações (Plotly)
    ├─> px.bar() - Gráficos de barras
    ├─> px.pie() - Gráficos de pizza
    ├─> px.histogram() - Histogramas
    └─> go.Figure() - Gráficos de linha customizados
```

### Dependências

```
┌─────────────────────────────────────────┐
│         Constantes Globais              │
│  - PADROES (OMS 2021)                   │
│  - CATEGORIAS_AQI                       │
└──────────────┬──────────────────────────┘
               │
               ├─> calcular_aqi_pm25()
               │   └─> (usa breakpoints implícitos)
               │
               └─> obter_categoria_aqi()
                   └─> (usa CATEGORIAS_AQI)
                       │
                       └─> processar_dados_semana()
                           │
                           └─> main()
                               └─> (usa em todas as tabs)
```

### Fluxo de Dados entre Funções

```
carregar_dados()
    │
    └─> retorna: {'semana': DataFrame, 'hoje': DataFrame}
        │
        └─> processar_dados_semana(df_semana)
            │
            ├─> calcula AQI: calcular_aqi_pm25(PM2.5)
            │   └─> retorna: número (0-500+)
            │
            └─> categoriza: obter_categoria_aqi(AQI)
                └─> retorna: ('Boa', '#00E400')
                    │
                    └─> DataFrame enriquecido
                        │
                        └─> usado em:
                            ├─> Agregações (groupby)
                            ├─> Filtros (query)
                            └─> Visualizações (Plotly)
```

---

## Estrutura de Dados

### Formato do CSV de Entrada (INPE)

O CSV baixado do INPE contém colunas como:

```csv
date,municipio,estado,pm2_5_media_diaria_previsao_situacao_atual,pm10_media_diaria_previsao_situacao_atual,o3_media_diaria_previsao_situacao_atual,...
2025-10-28,São Paulo,SP,12.5,25.3,85.2,...
2025-10-28,Rio de Janeiro,RJ,15.8,30.1,92.5,...
```

### DataFrame Processado

Após `processar_dados_semana()`, o DataFrame contém:

| Coluna | Tipo | Descrição |
|--------|------|------------|
| `date` | string | Data original do CSV |
| `data` | datetime | Data convertida para datetime |
| `municipio` | string | Nome do município |
| `estado` | string | Sigla do estado (UF) |
| `PM2.5` | float | Concentração de PM2.5 (µg/m³) |
| `PM10` | float | Concentração de PM10 (µg/m³) |
| `O3` | float | Concentração de O3 (µg/m³) |
| `AQI` | int | Índice de Qualidade do Ar (0-500+) |
| `Categoria` | string | Categoria AQI (Boa, Moderada, etc.) |
| `Cor` | string | Cor hexadecimal para visualização |

### Estruturas de Dados Internas

#### `PADROES` (Constante)

```python
PADROES = {
    'PM2.5': {'24h': 15, 'anual': 5, 'critico': 35},
    'PM10': {'24h': 45, 'anual': 15, 'critico': 150},
    'O3': {'8h': 100, 'critico': 160}
}
```

Usado para:
- Comparações com limites OMS
- Linhas de referência em gráficos
- Cálculo de deltas nas métricas

#### `CATEGORIAS_AQI` (Constante)

```python
CATEGORIAS_AQI = [
    {'nome': 'Boa', 'min': 0, 'max': 50, 'cor': '#00E400'},
    {'nome': 'Moderada', 'min': 51, 'max': 100, 'cor': '#FFFF00'},
    ...
]
```

Usado por:
- `obter_categoria_aqi()` para classificação
- Mapeamento de cores em gráficos de pizza
- Legenda de categorias

---

## Considerações Técnicas

### Performance

1. **Cache do Streamlit**: `@st.cache_data(ttl=300)` evita recarregar dados a cada interação
2. **Lazy Loading**: Dados são carregados apenas quando necessário
3. **Agregações Eficientes**: Uso de `groupby()` do Pandas para cálculos agregados

### Tratamento de Erros

- **Coleta**: Múltiplas tentativas de clique e fallbacks em JavaScript
- **Dashboard**: Validação de existência de arquivos e tratamento de DataFrames vazios
- **Dados Faltantes**: Uso de `pd.isna()` e `errors='coerce'` em conversões

### Escalabilidade

- O sistema pode processar milhares de registros (ex: 194.952 linhas no CSV de exemplo)
- Streamlit gerencia renderização eficiente de grandes DataFrames
- Plotly otimiza renderização de gráficos com muitos pontos

---

## Conclusão

Este sistema implementa um pipeline completo de coleta, processamento e visualização de dados de qualidade do ar, utilizando técnicas modernas de web scraping e visualização interativa. A arquitetura modular permite fácil manutenção e extensão, enquanto o uso de cache e agregações eficientes garante boa performance mesmo com grandes volumes de dados.

