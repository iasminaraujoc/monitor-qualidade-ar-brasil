# Testes - Monitor de Qualidade do Ar

## 📋 Estrutura de Testes

```
tests/
├── __init__.py                    # Inicialização do pacote de testes
├── conftest.py                    # Fixtures compartilhadas
├── pytest.ini                     # Configuração do pytest
├── test_dashboard_qualidade_ar.py # Testes unitários do dashboard
├── test_integracao.py             # Testes de integração
├── TESTES.md                      # Guia completo de testes
└── README.md                      # Este arquivo
```

## 🚀 Como Executar os Testes

### Instalar dependências de teste

```bash
pip install -r requirements.txt
```

### Executar todos os testes

**Da raiz do projeto:**
```bash
pytest tests/
```

**Ou de dentro da pasta tests:**
```bash
cd tests
pytest
```

### Executar testes com cobertura

```bash
pytest --cov=dashboard_qualidade_ar --cov-report=html
```

### Executar testes específicos

```bash
# Apenas testes unitários
pytest tests/test_dashboard_qualidade_ar.py

# Apenas testes de integração
pytest tests/test_integracao.py

# Teste específico
pytest tests/test_dashboard_qualidade_ar.py::TestCalcularAQIPM25::test_aqi_categoria_boa
```

### Executar com verbose

```bash
pytest -v
```

### Executar com output detalhado

```bash
pytest -vv -s
```

## 📊 Cobertura de Testes

Os testes cobrem:

### Funções Testadas

- ✅ `calcular_aqi_pm25()` - Cálculo de AQI para PM2.5
- ✅ `obter_categoria_aqi()` - Categorização baseada em AQI
- ✅ `processar_dados_semana()` - Processamento de DataFrames
- ✅ `carregar_dados()` - Carregamento de arquivos CSV

### Cenários Testados

1. **Cálculo de AQI**
   - Valores em todas as categorias (Boa, Moderada, Insalubre, etc.)
   - Valores nos limites entre categorias
   - Valores extremos (zero, muito altos)
   - Valores NaN (dados faltantes)

2. **Categorização**
   - Todas as 6 categorias de qualidade do ar
   - Valores nos limites entre categorias
   - Valores NaN

3. **Processamento de Dados**
   - Renomeação de colunas
   - Conversão de datas
   - Cálculo de AQI e categorização
   - Tratamento de valores faltantes
   - Valores extremos

4. **Carregamento de Dados**
   - Carregamento bem-sucedido
   - Pasta inexistente
   - Arquivos não encontrados
   - Erros ao ler CSV

5. **Integrações**
   - Fluxo completo de processamento
   - Consistência entre AQI e categoria
   - Agregações (por estado, data, município)
   - Casos extremos (DataFrame vazio, muitos dados)

## 🔧 Fixtures Disponíveis

### `dados_semana_raw`
DataFrame simulado com estrutura similar aos dados do INPE (6 registros)

### `dados_semana_processados`
DataFrame já processado com colunas normalizadas

### `dados_com_valores_faltantes`
DataFrame com valores NaN para testar tratamento de dados faltantes

### `dados_valores_extremos`
DataFrame com valores extremos para testar limites do AQI

### `pasta_downloads_temporaria`
Pasta temporária para simular `downloads_inpe/` (limpa automaticamente após testes)

### `arquivo_csv_semana`
Arquivo CSV simulado de semana epidemiológica

### `arquivo_csv_hoje`
Arquivo CSV simulado de dados do dia atual

### `concentracoes_pm25_teste`
Dicionário com concentrações de PM2.5 e AQI esperado

### `categorias_aqi_esperadas`
Mapeamento de AQI para categorias esperadas

## 📝 Exemplos de Uso

### Teste Unitário Simples

```python
def test_aqi_categoria_boa():
    resultado = calcular_aqi_pm25(6.0)
    assert resultado == 25
```

### Teste com Fixture

```python
def test_processar_dados_basico(dados_semana_raw):
    resultado = processar_dados_semana(dados_semana_raw)
    assert 'PM2.5' in resultado.columns
```

### Teste de Integração

```python
def test_fluxo_completo_processamento(dados_semana_raw):
    df_processado = processar_dados_semana(dados_semana_raw)
    # Verifica consistência entre funções
    for idx, row in df_processado.iterrows():
        if pd.notna(row['PM2.5']):
            aqi_esperado = calcular_aqi_pm25(row['PM2.5'])
            assert row['AQI'] == aqi_esperado
```

## 🐛 Troubleshooting

### Erro: ModuleNotFoundError

Certifique-se de que está executando os testes a partir do diretório raiz do projeto:

```bash
cd monitor-qualidade-ar-brasil
pytest
```

### Erro: ImportError

Verifique se todas as dependências estão instaladas:

```bash
pip install -r requirements.txt
```

### Testes falhando com dados reais

Os testes usam dados simulados. Se precisar testar com dados reais, ajuste os fixtures em `conftest.py`.

## 📈 Melhorias Futuras

- [ ] Testes para o módulo `coletar_inpe_sisam.py` (com mocks do Selenium)
- [ ] Testes de performance para grandes volumes de dados
- [ ] Testes de visualizações (Plotly)
- [ ] Testes end-to-end do dashboard Streamlit
- [ ] Integração contínua (CI/CD) com GitHub Actions

