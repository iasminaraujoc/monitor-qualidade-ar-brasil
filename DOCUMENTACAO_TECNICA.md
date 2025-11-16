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
- **`analise_tendencias.py`**: Módulo de análise estatística para detecção de tendências, projeções e anomalias
- **`alertas.py`**: Sistema de geração e gerenciamento de alertas de qualidade do ar

### Tecnologias Utilizadas

- **Selenium WebDriver**: Automação de navegador para scraping
- **Streamlit**: Framework para criação de dashboards interativos
- **Pandas**: Manipulação e processamento de dados
- **Plotly**: Visualizações interativas de gráficos
- **SciPy**: Análises estatísticas e regressões
- **NumPy**: Computação numérica e cálculos matriciais
- **Chrome/ChromeDriver**: Navegador automatizado para coleta

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
│  - dados_inpe_hoje_YYYYMMDD_HHMMSS.json (dados diários)   │
│  - dados_inpe_hoje_YYYYMMDD_HHMMSS.csv (dados diários)    │
│  - dados_inpe_semana_epidemiologica_municipios_*.csv       │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ Lê arquivos mais recentes
                        ▼
┌─────────────────────────────────────────────────────────────┐
│        dashboard_qualidade_ar.py (Módulo de Visualização)  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Funções de Processamento                            │  │
│  │  - carregar_dados() (lê JSON + CSV)                 │  │
│  │  - processar_dados_hoje() (processa JSON)           │  │
│  │  - extrair_valor_indicador() (regex para JSON)      │  │
│  │  - processar_dados_semana() (processa CSV)          │  │
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

#### `extrair_valor_indicador(texto, padrao)`

**Propósito**: Extrai valores numéricos de poluentes do texto dos indicadores usando expressões regulares.

**Parâmetros:**
- `texto`: String contendo os indicadores ambientais
- `padrao`: Expressão regular para capturar o valor do poluente

**Exemplo de texto de entrada:**
```
PM₂.₅
6.85 μg/m³
PM₁₀
7.01 μg/m³
O₃
19.00 μg/m³
```

**Padrões de regex utilizados:**
```python
{
    'PM2.5': r'PM[₂2]\.?[₅5]\n?([\d.]+)\s*[μµ]?g/m³',
    'PM10': r'PM[₁1][₀0]\n?([\d.]+)\s*[μµ]?g/m³',
    'O3': r'O[₃3]\n?([\d.]+)\s*[μµ]?g/m³',
    'SO2': r'SO[₂2]\n?([\d.]+)\s*[μµ]?g/m³',
    'NO2': r'NO[₂2]\n?([\d.]+)\s*[μµ]?g/m³'
}
```

**Retorno**: Valor numérico (float) ou `None` se não encontrado.

#### `processar_dados_hoje(dados_json)`

**Propósito**: Processa o JSON de dados diários coletados do INPE SISAM.

**Estrutura do JSON de entrada:**
```python
[
    {
        "estado": "AC",
        "estado_nome": "Acre",
        "data_coleta": "2025-11-08T17:54:05.659815",
        "indicadores": {
            "PM₂.₅\n6.85 μg/m³\n...": "...",
            ...
        }
    },
    ...
]
```

**Processamento:**
1. Itera sobre cada estado no JSON
2. Para cada estado, busca a chave do dicionário `indicadores` que contém o texto completo
3. Aplica `extrair_valor_indicador()` com regex para cada poluente
4. Cria DataFrame com valores extraídos
5. Calcula AQI e categoriza cada registro

**Retorno**: DataFrame processado com colunas:
- `estado`: Sigla do estado (UF)
- `estado_nome`: Nome completo do estado
- `data_coleta`: Timestamp da coleta
- `PM2.5`, `PM10`, `O3`, `SO2`, `NO2`: Concentrações extraídas
- `AQI`: Índice calculado
- `Categoria`: Classificação (Boa, Moderada, etc.)
- `Cor`: Cor hexadecimal para visualização

#### `carregar_dados()` (com cache)

```python
@st.cache_data(ttl=300)
def carregar_dados()
```

**Propósito**: Carrega os arquivos mais recentes da pasta `downloads_inpe/`.

**Funcionalidades:**
- Utiliza `glob` para encontrar arquivos que seguem padrões específicos:
  - `dados_inpe_semana_*.csv` para dados de semana epidemiológica
  - `dados_inpe_hoje_*.json` para dados diários (JSON)
- Identifica o arquivo mais recente usando `os.path.getctime()`
- **Dados Semanais**: Carrega CSV com `pd.read_csv()`
- **Dados Diários**: 
  - Carrega JSON com `json.load()`
  - Processa com `processar_dados_hoje()` para criar DataFrame
- Retorna dicionário com DataFrames e nomes dos arquivos

**Cache**: Utiliza `@st.cache_data(ttl=300)` para cachear resultados por 5 minutos, evitando recarregar dados desnecessariamente.

**Retorno:**
```python
{
    'semana': DataFrame,                      # Dados semanais (CSV)
    'arquivo_semana': 'dados_inpe_semana_...csv',
    'hoje': DataFrame,                        # Dados diários (JSON processado)
    'arquivo_hoje': 'dados_inpe_hoje_...json'
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

   **Tab 1: Visão Geral** _(Usa dados diários do JSON)_
   - **Métricas Principais**: 4 colunas com KPIs
     - Total de estados (27)
     - PM2.5 médio nacional (com delta vs OMS)
     - PM10 médio nacional (com delta vs OMS)
     - Data/hora da última coleta
   
   - **Gráfico de Barras por Estado**
     - Todos os 27 estados com concentração atual de PM2.5
     - Estados ordenados do maior para o menor valor
     - Linha de referência do limite OMS (15 µg/m³)
     - Hover mostra PM10 e O3 adicionalmente
     - Utiliza Plotly Express (`px.bar`)
   
   - **Distribuição de Categorias**
     - **Gráfico de Pizza**: Proporção de cada categoria AQI entre os estados
     - **Gráfico de Barras Comparativo**: Média Brasil vs Limite OMS
       - 3 poluentes lado a lado (PM2.5, PM10, O3)
       - Comparação visual entre valores medidos e limites OMS
   
   - **Estatísticas por Estado (Hoje)**
     - 3 colunas (PM2.5, PM10, O3)
     - **Estados acima do limite OMS**: Contagem e percentual
     - **Valores máximo e mínimo**: Faixa de variação entre estados
     - Foco em dados do dia atual para análise em tempo real

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
   
   **Tab 5: Alertas**
   - **Sistema de Alertas Inteligente**: Detecta estados e municípios com concentrações críticas
   - **Filtros por Tipo**: Estados ou Municípios
   - **Níveis de Alerta**: Crítico, Alerta OMS e Melhorias
   - **Paginação**: Navegação entre páginas de alertas
   - **Estatísticas Dinâmicas**: Contadores por tipo de alerta
   - **Recomendações**: Orientações por categoria de qualidade do ar
   
   **Tab 6: Análise de Tendências** _(NOVO)_
   - **Filtros Avançados**: Por poluente, estado e município
   - **Tendência Linear**:
     - Regressão linear com coeficiente de determinação (R²)
     - Taxa de mudança diária e percentual
     - Interpretação estatística (p-value)
     - Classificação: crescente, decrescente ou estável
   - **Projeções Futuras**:
     - Projeção de 7 dias baseada em tendência linear
     - Intervalo de confiança de 95%
     - Visualização integrada com dados históricos
   - **Análise de Sazonalidade**:
     - Padrões por dia da semana
     - Padrões mensais
     - Identificação de períodos críticos
   - **Análise de Volatilidade**:
     - Medidas de tendência central (média, mediana)
     - Medidas de dispersão (desvio padrão, amplitude)
     - Coeficiente de variação
     - Box plot de distribuição
   - **Detecção de Anomalias**:
     - Método Z-score (> 2.5 desvios padrão)
     - Classificação: anomalias altas e baixas
     - Visualização temporal de anomalias
     - Tabela detalhada de ocorrências

4. **Rodapé**
   - Informações sobre fonte de dados e padrões utilizados

---

## Módulo de Análise de Tendências

### Classe: `AnalisadorTendencias`

Este módulo fornece ferramentas estatísticas avançadas para análise temporal de dados de qualidade do ar.

#### Inicialização

```python
analisador = AnalisadorTendencias(df, coluna_data='data')
```

**Parâmetros:**
- `df`: DataFrame com dados históricos
- `coluna_data`: Nome da coluna contendo timestamps (padrão: 'data')

**Funcionalidades Principais:**

#### 1. Análise de Tendência Linear

```python
tendencia = analisador.calcular_tendencia_linear(
    poluente='PM2.5',
    estado='SP',
    municipio='São Paulo'
)
```

**Método Estatístico:** Regressão Linear Simples (scipy.stats.linregress)

**Retorna:**
- `slope`: Taxa de mudança (µg/m³ por dia)
- `intercept`: Valor inicial estimado
- `r_squared`: Coeficiente de determinação (0-1)
- `p_value`: Significância estatística
- `tendencia`: Classificação ('crescente', 'decrescente', 'estável')
- `taxa_mudanca_percentual`: Mudança percentual diária

**Critérios de Classificação:**
- **Crescente**: slope > 0.1 e p < 0.05
- **Decrescente**: slope < -0.1 e p < 0.05
- **Estável**: |slope| ≤ 0.1 ou p ≥ 0.05

#### 2. Projeções Futuras

```python
projecao = analisador.projetar_valores_futuros(
    poluente='PM2.5',
    dias_futuros=7,
    estado='SP'
)
```

**Método:** Extrapolação linear com intervalo de confiança de 95%

**Retorna DataFrame com:**
- `data`: Datas futuras projetadas
- `valor_projetado`: Valor estimado
- `limite_inferior`: Limite inferior do IC 95%
- `limite_superior`: Limite superior do IC 95%

**Fórmula:**
```
valor_projetado = intercept + slope * dias_desde_inicio
margem_erro = 1.96 * erro_padrao * sqrt(dias_desde_inicio)
```

#### 3. Análise de Sazonalidade

```python
sazonalidade = analisador.analisar_sazonalidade(
    poluente='PM2.5',
    estado='SP'
)
```

**Retorna:**
- `por_dia_semana`: Estatísticas por dia da semana (média, std, count)
- `por_mes`: Estatísticas mensais
- `dia_semana_maior/menor`: Dias com maiores/menores concentrações
- `mes_maior/menor`: Meses com maiores/menores concentrações
- `variacao_semanal/mensal`: Desvio padrão das médias

**Uso:** Identificar padrões temporais recorrentes

#### 4. Análise de Volatilidade

```python
volatilidade = analisador.calcular_volatilidade(
    poluente='PM2.5',
    estado='SP'
)
```

**Métricas Calculadas:**

**Tendência Central:**
- Média aritmética
- Mediana (P50)

**Dispersão:**
- Desvio padrão
- Coeficiente de variação (CV = std/mean * 100)
- Amplitude (max - min)
- Amplitude interquartil (P75 - P25)
- Percentis 25 e 75

**Interpretação do Coeficiente de Variação:**
- CV < 15%: Baixa volatilidade (dados homogêneos)
- 15% ≤ CV < 30%: Volatilidade moderada
- CV ≥ 30%: Alta volatilidade (dados heterogêneos)

#### 5. Detecção de Anomalias

```python
anomalias = analisador.detectar_anomalias(
    poluente='PM2.5',
    limite_desvios=2.5,
    estado='SP'
)
```

**Método:** Z-score (Desvios Padrão da Média)

**Fórmula:**
```
z_score = (valor - média) / desvio_padrão
anomalia = |z_score| > limite_desvios
```

**Padrão:** limite_desvios = 2.5 (captura ~99% dos valores em distribuição normal)

**Retorna DataFrame com:**
- `data`: Data da anomalia
- `poluente`: Valor anômalo
- `z_score`: Número de desvios padrão
- `tipo`: 'Alta' (z > 0) ou 'Baixa' (z < 0)

**Interpretação:**
- Z-score > 2.5: Valor anormalmente alto
- Z-score < -2.5: Valor anormalmente baixo

#### 6. Comparação de Períodos

```python
comparacao = analisador.comparar_periodos(
    poluente='PM2.5',
    periodo1_inicio='2025-10-01',
    periodo1_fim='2025-10-15',
    periodo2_inicio='2025-10-16',
    periodo2_fim='2025-10-31',
    estado='SP'
)
```

**Método:** Teste t de Student para amostras independentes

**Retorna:**
- Estatísticas de cada período (média, mediana, std)
- `mudanca_absoluta`: Diferença entre médias
- `mudanca_percentual`: Variação percentual
- `t_statistic`: Estatística do teste t
- `p_value`: Significância da diferença
- `diferenca_significativa`: Boolean (p < 0.05)
- `interpretacao`: Descrição textual

#### 7. Média Móvel

```python
df_ma = analisador.calcular_media_movel(
    poluente='PM2.5',
    janela=7,
    estado='SP'
)
```

**Método:** Rolling mean (janela deslizante)

**Uso:** Suavizar ruído e identificar tendências subjacentes

**Retorna DataFrame com:**
- `data`: Datas
- `poluente`: Valores originais
- `{poluente}_MA{janela}`: Média móvel

#### 8. Relatório Completo

```python
relatorio = analisador.gerar_relatorio_completo(
    poluente='PM2.5',
    estado='SP'
)
```

**Retorna dicionário com:**
- `tendencia_linear`: Análise de tendência
- `volatilidade`: Métricas de dispersão
- `sazonalidade`: Padrões temporais
- `anomalias`: DataFrame de anomalias
- `projecao_7_dias`: Projeções futuras

### Funções Auxiliares

Para uso rápido sem instanciar a classe:

```python
from analise_tendencias import calcular_tendencia, projetar_futuro, detectar_anomalias

# Uso direto
tendencia = calcular_tendencia(df, 'PM2.5', estado='SP')
projecao = projetar_futuro(df, 'PM2.5', dias=7)
anomalias = detectar_anomalias(df, 'PM2.5')
```

### Visualizações no Dashboard

A Tab "Análise de Tendências" integra todas essas análises em visualizações interativas:

1. **Gráfico de Tendência e Projeção**
   - Scatter plot dos valores observados
   - Linha de regressão linear
   - Projeção futura com intervalo de confiança
   - Linha de referência OMS

2. **Gráficos de Sazonalidade**
   - Barras: Médias por dia da semana
   - Barras: Médias mensais
   - Barras de erro mostrando desvio padrão

3. **Box Plot de Volatilidade**
   - Visualização da distribuição completa
   - Quartis, mediana e outliers
   - Média e desvio padrão

4. **Gráfico de Anomalias**
   - Valores normais vs. anomalias
   - Destacado com marcadores em X vermelho
   - Timeline temporal

### Considerações Técnicas

**Performance:**
- Cálculos vetorizados com NumPy para eficiência
- Cache de Streamlit para evitar recálculos desnecessários

**Requisitos de Dados:**
- Mínimo 3 observações para tendência linear
- Mínimo 7 observações para sazonalidade semanal
- Mínimo 5 observações para detecção de anomalias

**Limitações:**
- Regressão linear assume relação linear (pode não capturar padrões complexos)
- Projeções são válidas apenas para curto prazo (7 dias recomendado)
- Detecção de anomalias assume distribuição aproximadamente normal

**Bibliotecas Utilizadas:**
- `scipy.stats`: Regressões e testes estatísticos
- `numpy`: Cálculos numéricos
- `pandas`: Manipulação de dados temporais

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
               ├─> glob.glob() encontra arquivos mais recentes
               │   ├─> JSON (dados diários): json.load()
               │   │   └─> processar_dados_hoje()
               │   │       └─> extrair_valor_indicador() com regex
               │   │           └─> calcular_aqi_pm25()
               │   │               └─> obter_categoria_aqi()
               │   │                   └─> DataFrame de estados
               │   └─> CSV (dados semanais): pd.read_csv()
               │       └─> processar_dados_semana()
               │           └─> Normaliza colunas
               │               └─> calcular_aqi_pm25() para cada registro
               │                   └─> obter_categoria_aqi() para cada AQI
               │                       └─> DataFrame de municípios
               └─> Retorna dicionário com ambos DataFrames
                   └─> Tab 1 (Visão Geral): usa df_hoje (estados)
                   └─> Tabs 2-4: usam df_semana (municípios)
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
│   ├─> glob.glob() - Encontra arquivos JSON e CSV
│   ├─> json.load() - Carrega dados diários
│   │   └─> processar_dados_hoje(dados_json)
│   │       ├─> extrair_valor_indicador(texto, padrao) [para cada poluente]
│   │       ├─> calcular_aqi_pm25(concentracao)
│   │       └─> obter_categoria_aqi(aqi)
│   └─> pd.read_csv() - Carrega dados semanais
│       └─> processar_dados_semana(df)
│           ├─> calcular_aqi_pm25(concentracao)
│           └─> obter_categoria_aqi(aqi)
│               └─> (usa CATEGORIAS_AQI)
│
└─> Visualizações por Tab
    ├─> Tab 1 (Visão Geral): usa df_hoje
    │   ├─> px.bar() - Barras por estado
    │   ├─> px.pie() - Distribuição de categorias
    │   └─> go.Figure() - Comparativo vs OMS
    │
    └─> Tabs 2-4: usam df_semana
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
                       ├─> processar_dados_hoje()
                       │   ├─> extrair_valor_indicador()
                       │   │   └─> (usa regex patterns)
                       │   └─> (cria DataFrame de estados)
                       │
                       ├─> processar_dados_semana()
                       │   └─> (cria DataFrame de municípios)
                       │
                       └─> main()
                           ├─> Tab 1: usa df_hoje (estados)
                           └─> Tabs 2-4: usam df_semana (municípios)
```

### Fluxo de Dados entre Funções

```
carregar_dados()
    │
    ├─> Processa JSON (dados diários)
    │   └─> processar_dados_hoje(dados_json)
    │       ├─> extrai valores: extrair_valor_indicador(texto, padrao)
    │       │   └─> retorna: float (ex: 6.85)
    │       ├─> calcula AQI: calcular_aqi_pm25(PM2.5)
    │       │   └─> retorna: número (0-500+)
    │       └─> categoriza: obter_categoria_aqi(AQI)
    │           └─> retorna: ('Boa', '#00E400')
    │               └─> df_hoje (27 estados)
    │
    └─> Processa CSV (dados semanais)
        └─> processar_dados_semana(df_semana)
            │
            ├─> calcula AQI: calcular_aqi_pm25(PM2.5)
            │   └─> retorna: número (0-500+)
            │
            └─> categoriza: obter_categoria_aqi(AQI)
                └─> retorna: ('Boa', '#00E400')
                    │
                    └─> df_semana (~195k registros)
                        │
                        └─> usado em:
                            ├─> Agregações (groupby)
                            ├─> Filtros (query)
                            └─> Visualizações (Plotly)
    │
    └─> retorna: {
        'semana': df_semana,
        'hoje': df_hoje,
        'arquivo_semana': 'nome.csv',
        'arquivo_hoje': 'nome.json'
    }
```

---

## Estrutura de Dados

### Formato do JSON de Dados Diários (INPE)

O JSON gerado pelo coletor contém dados por estado:

```json
[
  {
    "estado": "AC",
    "estado_nome": "Acre",
    "data_coleta": "2025-11-08T17:54:05.659815",
    "indicadores": {
      "INDICADORES AMBIENTAIS\nPM₂.₅\n6.85 μg/m³\nPM₁₀\n7.01 μg/m³\nSO₂\n0.06 μg/m³\nNO₂\n0.71 μg/m³\nO₃\n19.00 μg/m³\nCO\n0.17 ppm\nTemp.\n-\nPrec.\n-\nFocos\n-": "...",
      "PM₂.₅\n6.85 μg/m³": "PM₂.₅\n6.85 μg/m³",
      ...
    }
  },
  ...
]
```

**Nota**: Os valores ficam nas chaves do dicionário `indicadores` como strings formatadas. A função `extrair_valor_indicador()` usa regex para extrair os valores numéricos.

### Formato do CSV de Entrada (INPE - Dados Semanais)

O CSV baixado do INPE contém colunas como:

```csv
date,municipio,estado,pm2_5_media_diaria_previsao_situacao_atual,pm10_media_diaria_previsao_situacao_atual,o3_media_diaria_previsao_situacao_atual,...
2025-10-28,São Paulo,SP,12.5,25.3,85.2,...
2025-10-28,Rio de Janeiro,RJ,15.8,30.1,92.5,...
```

### DataFrame Processado (Dados Diários)

Após `processar_dados_hoje()`, o DataFrame contém:

| Coluna | Tipo | Descrição |
|--------|------|------------|
| `estado` | string | Sigla do estado (UF) |
| `estado_nome` | string | Nome completo do estado |
| `data_coleta` | datetime | Timestamp da coleta |
| `PM2.5` | float | Concentração de PM2.5 (µg/m³) |
| `PM10` | float | Concentração de PM10 (µg/m³) |
| `O3` | float | Concentração de O3 (µg/m³) |
| `SO2` | float | Concentração de SO2 (µg/m³) |
| `NO2` | float | Concentração de NO2 (µg/m³) |
| `AQI` | int | Índice de Qualidade do Ar (0-500+) |
| `Categoria` | string | Categoria AQI (Boa, Moderada, etc.) |
| `Cor` | string | Cor hexadecimal para visualização |

**Uso**: Tab "Visão Geral" (27 registros - um por estado)

### DataFrame Processado (Dados Semanais)

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

**Uso**: Tabs "Série Temporal", "Rankings" e "Dados Brutos" (~195.000 registros - dados históricos de 5 semanas)

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

### Estratégia de Dados Híbrida

O sistema utiliza uma abordagem híbrida inteligente:

1. **Dados Diários (JSON)**: 
   - Fonte: Coleta por estado via Selenium
   - Volume: 27 registros (um por estado)
   - Uso: Tab "Visão Geral" para análise em tempo real
   - Vantagem: Dados mais recentes, leves e rápidos de processar

2. **Dados Históricos (CSV)**:
   - Fonte: Download de semana epidemiológica
   - Volume: ~195.000 registros (5 semanas × todos municípios)
   - Uso: Tabs "Série Temporal", "Rankings" e "Dados Brutos"
   - Vantagem: Análise detalhada por município e tendências temporais

Esta separação otimiza a experiência do usuário:
- **Visão rápida**: Dados diários carregam instantaneamente
- **Análise profunda**: Dados históricos disponíveis para investigação detalhada
- **Melhor UX**: Diferentes níveis de granularidade para diferentes necessidades

### Processamento com Regex

A extração de dados do JSON usa expressões regulares para lidar com a estrutura não-padronizada dos indicadores ambientais retornados pelo INPE. Isso torna o sistema resiliente a pequenas mudanças no formato da página fonte, mantendo a robustez da coleta.

