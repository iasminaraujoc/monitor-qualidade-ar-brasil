# 📖 Guia de Uso - Dashboard de Qualidade do Ar

## 🚀 Início Rápido (3 passos)

### 1️⃣ Ativar ambiente virtual
```bash
cd /home/iasmin-araujo/Documents/monitor-qualidade-ar-brasil
source venv/bin/activate
```

### 2️⃣ Coletar dados (se necessário)
```bash
python3 coletar_inpe_sisam.py
```

### 3️⃣ Iniciar dashboard
```bash
streamlit run dashboard_qualidade_ar.py
```

**OU use o script auxiliar:**
```bash
./iniciar_dashboard.sh
```

## 📊 Abas do Dashboard

### 📍 Visão Geral
**O que você encontra:**
- 📈 **Métricas principais**: Total de municípios monitorados e concentrações médias
- 🗺️ **Ranking por estado**: Top 15 estados com maior concentração de PM2.5
- 🎯 **Distribuição de categorias**: Quantos municípios estão em cada categoria (Boa, Moderada, Insalubre, etc.)
- 📊 **Histograma**: Distribuição de concentrações de PM2.5
- 🔢 **Estatísticas gerais**: Quantos municípios estão acima dos limites OMS

**Para que serve:**
- Ter uma visão panorâmica da qualidade do ar no Brasil
- Identificar rapidamente estados com problemas
- Comparar situação atual com padrões da OMS

---

### 📈 Série Temporal
**O que você encontra:**
- 📉 **Gráfico de evolução**: Concentrações de PM2.5, PM10 e O3 ao longo das últimas 5 semanas
- 🎛️ **Filtros**: Selecione estado e município específicos
- 📏 **Linhas de referência**: Limites OMS marcados no gráfico
- 📊 **Estatísticas do período**: Valores mínimo, médio e máximo

**Para que serve:**
- Identificar tendências (melhora ou piora)
- Comparar períodos diferentes
- Analisar municípios específicos

**Como usar:**
1. Selecione um estado no primeiro filtro (ou deixe "Todos")
2. Se selecionou um estado, escolha um município (ou deixe "Todos")
3. O gráfico será atualizado automaticamente

---

### 🏆 Rankings
**O que você encontra:**
- ✅ **Top 10 melhores**: Municípios com melhor qualidade do ar
- ⚠️ **Top 10 piores**: Municípios com pior qualidade do ar
- 📊 **Gráfico comparativo**: Visualização lado a lado
- 🔄 **Seletor de poluente**: Alterne entre PM2.5, PM10, O3 ou AQI

**Para que serve:**
- Identificar melhores práticas (o que fazem os municípios com melhor qualidade?)
- Alertar sobre áreas críticas
- Comparar diferentes poluentes

**Como usar:**
1. Selecione o poluente no dropdown
2. Veja as duas tabelas (melhores e piores)
3. Analise o gráfico comparativo

---

### 📋 Dados Brutos
**O que você encontra:**
- 📄 **Tabela completa**: Todos os dados coletados
- 🔍 **Filtros**: Por estado e categoria de qualidade
- ⬇️ **Downloads**: Baixe os dados em CSV

**Para que serve:**
- Análises personalizadas
- Exportar dados para outras ferramentas
- Verificar valores específicos

**Como usar:**
1. Use os filtros multiselect para refinar os dados
2. Navegue pela tabela
3. Clique em "Baixar Dados" para exportar

## 🎨 Como Interpretar as Cores

| Cor | Categoria | O que significa |
|-----|-----------|-----------------|
| 🟢 Verde | Boa (0-50) | Ar limpo e seguro para todos |
| 🟡 Amarelo | Moderada (51-100) | Aceitável, mas pode afetar pessoas sensíveis |
| 🟠 Laranja | Insalubre p/ Sensíveis (101-150) | Grupos sensíveis devem reduzir atividades ao ar livre |
| 🔴 Vermelho | Insalubre (151-200) | Todos podem começar a sentir efeitos na saúde |
| 🟣 Roxo | Muito Insalubre (201-300) | Alerta de saúde: todos podem ter efeitos mais sérios |
| 🟤 Marrom | Perigosa (301+) | Alerta de emergência: todos devem evitar atividades ao ar livre |

## 🌍 Padrões da OMS

### PM2.5 (Material Particulado Fino)
- **24 horas**: 15 µg/m³
- **Anual**: 5 µg/m³
- **Crítico**: 35 µg/m³

### PM10 (Material Particulado)
- **24 horas**: 45 µg/m³
- **Anual**: 15 µg/m³
- **Crítico**: 150 µg/m³

### O3 (Ozônio)
- **8 horas**: 100 µg/m³
- **Crítico**: 160 µg/m³

## 💡 Dicas de Uso

### Para Pesquisadores
- Use a aba **Dados Brutos** para exportar dados
- Analise **Séries Temporais** para identificar padrões sazonais
- Compare **Rankings** entre diferentes poluentes

### Para Gestores Públicos
- Monitore os **Rankings** para identificar municípios que precisam de atenção
- Use a **Visão Geral** em apresentações
- Acompanhe a **Evolução Temporal** para medir eficácia de políticas

### Para Cidadãos
- Verifique a qualidade do ar do seu município na **Série Temporal**
- Use as cores para entender o risco à saúde
- Compartilhe informações sobre municípios em situação crítica

## 🔄 Atualização dos Dados

### Manual
```bash
python3 coletar_inpe_sisam.py
```

### Automática (Cron Job)
Adicione ao crontab:
```bash
# Atualizar diariamente às 6h
0 6 * * * cd /home/iasmin-araujo/Documents/monitor-qualidade-ar-brasil && source venv/bin/activate && python3 coletar_inpe_sisam.py
```

## 🆘 Problemas Comuns

### Dashboard não mostra dados
**Solução:** Verifique se existe arquivo CSV em `downloads_inpe/`
```bash
ls downloads_inpe/*.csv
```

### Gráficos não carregam
**Solução:** Limpe o cache do Streamlit
```bash
streamlit cache clear
```

### Erro ao coletar dados
**Solução:** Verifique conexão com internet e tente novamente

## 📱 Acessar de outros dispositivos

O dashboard está rodando em:
- **Local**: http://localhost:8501
- **Rede local**: http://192.168.0.18:8501 (verifique seu IP)

Para acessar de outros dispositivos na mesma rede, use o endereço de rede local.

## ⌨️ Atalhos do Streamlit

- **R**: Rerun (atualizar dashboard)
- **C**: Limpar cache
- **?**: Mostrar atalhos

## 📧 Suporte

Para dúvidas ou problemas:
1. Verifique este guia
2. Consulte o README.md
3. Abra uma issue no repositório

---

**Aproveite o dashboard! 🌫️📊**

