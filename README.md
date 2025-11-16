# 🌫️ Monitor de Qualidade do Ar - Brasil

Sistema de monitoramento e visualização da qualidade do ar no Brasil, utilizando dados do INPE SISAM (Sistema de Informações Ambientais Integrado à Saúde).

## 📋 Sobre o Projeto

Este projeto coleta e visualiza dados de qualidade do ar de milhares de municípios brasileiros, incluindo:
- **PM2.5**: Material particulado fino (≤ 2.5 µm)
- **PM10**: Material particulado (≤ 10 µm)
- **O3**: Ozônio troposférico

Os dados são comparados com os padrões estabelecidos pela **Organização Mundial da Saúde (OMS)** de 2021.

## 🚀 Início Rápido

### 1. Clonar o repositório
```bash
git clone <url-do-repositorio>
cd monitor-qualidade-ar-brasil
```

### 2. Criar ambiente virtual e instalar dependências
```bash
python3 -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Coletar dados do INPE SISAM
```bash
python3 coletar_inpe_sisam.py
```

Este script irá:
- ✅ Coletar dados do dia atual para todos os estados
- ✅ Baixar dados das últimas 5 semanas epidemiológicas para todos os municípios
- ✅ Salvar os dados em `downloads_inpe/`

### 4. Executar o dashboard
```bash
streamlit run dashboard_qualidade_ar.py
```

O dashboard estará disponível em: **http://localhost:8501**

## 📊 Funcionalidades do Dashboard

### 🏠 Visão Geral
- Métricas principais (total de municípios, médias de poluentes)
- Concentração média por estado
- Distribuição de categorias de qualidade do ar
- Estatísticas gerais (quantos municípios acima do limite OMS)

### 🚨 Sistema de Alertas
- Alertas automáticos para estados e municípios com concentrações críticas
- Níveis de alerta: Crítico (PM2.5 > 35 µg/m³), Alerta OMS (PM2.5 > 15 µg/m³)
- Paginação de alertas (20 por página)
- Estatísticas dinâmicas por filtro
- Recomendações de saúde por categoria

### 📈 Série Temporal
- Evolução temporal dos poluentes
- Filtros por estado e município
- Comparação com limites OMS
- Estatísticas do período selecionado

### 🏆 Rankings
- Top 10 municípios com melhor qualidade do ar
- Top 10 municípios com pior qualidade do ar
- Gráficos comparativos por poluente

### 📋 Dados Brutos
- Visualização completa dos dados
- Filtros por estado e categoria
- Download em CSV (filtrado ou completo)

### 📊 Análise de Tendências 🆕
**Funcionalidade avançada de análise estatística:**

#### 📈 Tendência Linear
- Regressão linear com coeficiente de determinação (R²)
- Taxa de mudança diária e percentual
- Classificação: crescente, decrescente ou estável
- Interpretação de significância estatística (p-value)

#### 🔮 Projeções Futuras
- Projeção de 7 dias baseada em tendência linear
- Intervalo de confiança de 95%
- Visualização integrada com dados históricos
- Linha de referência OMS

#### 📅 Análise de Sazonalidade
- Padrões por dia da semana
- Padrões mensais
- Identificação de períodos críticos
- Gráficos com barras de erro

#### 📊 Análise de Volatilidade
- Medidas de tendência central (média, mediana)
- Medidas de dispersão (desvio padrão, amplitude)
- Coeficiente de variação
- Box plot de distribuição
- Percentis e amplitude interquartil

#### 🔍 Detecção de Anomalias
- Método Z-score (> 2.5 desvios padrão)
- Classificação: anomalias altas e baixas
- Visualização temporal de anomalias
- Tabela detalhada de ocorrências anômalas

## 📁 Estrutura do Projeto

```
monitor-qualidade-ar-brasil/
├── coletar_inpe_sisam.py       # Script de coleta de dados
├── dashboard_qualidade_ar.py   # Dashboard Streamlit
├── analise_tendencias.py       # Módulo de análise estatística 🆕
├── alertas.py                  # Sistema de alertas
├── requirements.txt            # Dependências Python
├── iniciar_dashboard.sh        # Script de inicialização
├── downloads_inpe/             # Dados coletados
│   ├── dados_inpe_hoje_*.json
│   └── dados_inpe_semana_*.csv
├── DOCUMENTACAO_TECNICA.md     # Documentação técnica completa
└── README.md                   # Este arquivo
```

## 🔧 Requisitos do Sistema

- **Python**: 3.8 ou superior
- **Google Chrome**: Para coleta de dados com Selenium
- **ChromeDriver**: Instalado automaticamente via webdriver-manager

## 📦 Dependências Principais

- `streamlit`: Framework para criação do dashboard
- `pandas`: Manipulação e análise de dados
- `plotly`: Visualizações interativas
- `selenium`: Automação web para coleta de dados
- `beautifulsoup4`: Parsing de HTML
- `scipy`: Análises estatísticas e regressões 🆕
- `numpy`: Computação numérica 🆕

## 🌍 Padrões OMS 2021

| Poluente | Período | Limite (µg/m³) |
|----------|---------|----------------|
| PM2.5    | 24h     | 15             |
| PM2.5    | Anual   | 5              |
| PM10     | 24h     | 45             |
| PM10     | Anual   | 15             |
| O3       | 8h      | 100            |

## 🎨 Categorias de Qualidade do Ar (AQI)

| Categoria | AQI | Cor | Descrição |
|-----------|-----|-----|-----------|
| Boa | 0-50 | 🟢 Verde | Ar limpo, seguro para todos |
| Moderada | 51-100 | 🟡 Amarelo | Aceitável, pode afetar pessoas sensíveis |
| Insalubre p/ Sensíveis | 101-150 | 🟠 Laranja | Grupos sensíveis podem sentir efeitos |
| Insalubre | 151-200 | 🔴 Vermelho | Todos podem sentir efeitos na saúde |
| Muito Insalubre | 201-300 | 🟣 Roxo | Alerta de saúde |
| Perigosa | 301+ | 🟤 Marrom | Alerta de emergência |

## 🔄 Automatização

Para atualizar os dados automaticamente, você pode criar um cron job:

```bash
# Editar crontab
crontab -e

# Adicionar linha para executar diariamente às 6h da manhã
0 6 * * * cd /caminho/para/monitor-qualidade-ar-brasil && /caminho/para/venv/bin/python3 coletar_inpe_sisam.py
```

## 🐛 Solução de Problemas

### Erro: ChromeDriver não encontrado
```bash
# Instalar ChromeDriver manualmente
sudo apt-get install chromium-chromedriver  # Ubuntu/Debian
```

### Erro: Timeout ao coletar dados
- Verifique sua conexão com a internet
- O site do INPE pode estar temporariamente indisponível
- Tente novamente mais tarde

### Dashboard não carrega dados
- Verifique se os arquivos CSV estão na pasta `downloads_inpe/`
- Execute primeiro: `python3 coletar_inpe_sisam.py`

## 📄 Fonte dos Dados

- **INPE SISAM**: https://queimadas.dgi.inpe.br/queimadas/portal/sisam
- Sistema de Informações Ambientais Integrado à Saúde Ambiental
- Dados de previsão de qualidade do ar baseados em modelagem numérica

## 📝 Licença

Este projeto é de código aberto para fins educacionais e informativos.

## ⚠️ Aviso Legal

Os dados apresentados são para fins informativos. Para decisões críticas relacionadas à saúde, consulte fontes oficiais e profissionais de saúde.

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:
- Reportar bugs
- Sugerir novas funcionalidades
- Melhorar a documentação
- Submeter pull requests

## 📧 Contato

Para dúvidas ou sugestões, abra uma issue no repositório.

---

**Desenvolvido com ❤️ para monitoramento da qualidade do ar no Brasil**
