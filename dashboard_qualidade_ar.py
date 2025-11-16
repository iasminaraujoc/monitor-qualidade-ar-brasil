"""
Dashboard de Qualidade do Ar - Brasil
Lê dados dos CSVs coletados do INPE SISAM
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import glob
import os
import json
import re
from alertas import gerar_todos_alertas, NIVEIS_ALERTA, obter_recomendacao_categoria

# Configuração da página
st.set_page_config(
    page_title="Monitor Qualidade do Ar - Brasil",
    page_icon="🌫️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Padrões de qualidade do ar (OMS 2021)
PADROES = {
    'PM2.5': {'24h': 15, 'anual': 5, 'critico': 35},
    'PM10': {'24h': 45, 'anual': 15, 'critico': 150},
    'O3': {'8h': 100, 'critico': 160}
}

CATEGORIAS_AQI = [
    {'nome': 'Boa', 'min': 0, 'max': 50, 'cor': '#00E400'},
    {'nome': 'Moderada', 'min': 51, 'max': 100, 'cor': '#FFFF00'},
    {'nome': 'Insalubre p/ Sensíveis', 'min': 101, 'max': 150, 'cor': '#FF7E00'},
    {'nome': 'Insalubre', 'min': 151, 'max': 200, 'cor': '#FF0000'},
    {'nome': 'Muito Insalubre', 'min': 201, 'max': 300, 'cor': '#8F3F97'},
    {'nome': 'Perigosa', 'min': 301, 'max': 500, 'cor': '#7E0023'}
]

def calcular_aqi_pm25(concentracao):
    """Calcula AQI para PM2.5"""
    if pd.isna(concentracao):
        return None
    
    if concentracao <= 12:
        return round(concentracao * 50 / 12)
    elif concentracao <= 35.4:
        return round(50 + (concentracao - 12) * 50 / 23.4)
    elif concentracao <= 55.4:
        return round(100 + (concentracao - 35.4) * 50 / 20)
    elif concentracao <= 150.4:
        return round(150 + (concentracao - 55.4) * 50 / 95)
    elif concentracao <= 250.4:
        return round(200 + (concentracao - 150.4) * 100 / 100)
    else:
        return round(300 + (concentracao - 250.4) * 200 / 250)

def obter_categoria_aqi(aqi):
    """Retorna categoria baseada no AQI"""
    if pd.isna(aqi):
        return 'Sem dados', '#CCCCCC'
    
    for cat in CATEGORIAS_AQI:
        if cat['min'] <= aqi <= cat['max']:
            return cat['nome'], cat['cor']
    
    return 'Perigosa', '#7E0023'

def extrair_valor_indicador(texto, padrao):
    """Extrai valor numérico de um poluente do texto dos indicadores"""
    if not texto or not isinstance(texto, str):
        return None
    
    match = re.search(padrao, texto, re.IGNORECASE)
    
    if match:
        try:
            return float(match.group(1))
        except:
            return None
    return None

def processar_dados_hoje(dados_json):
    """Processa dados diários do JSON"""
    if not dados_json:
        return None
    
    registros = []
    
    # Padrões de regex para cada poluente
    padroes = {
        'PM2.5': r'PM[₂2]\.?[₅5]\n?([\d.]+)\s*[μµ]?g/m³',
        'PM10': r'PM[₁1][₀0]\n?([\d.]+)\s*[μµ]?g/m³',
        'O3': r'O[₃3]\n?([\d.]+)\s*[μµ]?g/m³',
        'SO2': r'SO[₂2]\n?([\d.]+)\s*[μµ]?g/m³',
        'NO2': r'NO[₂2]\n?([\d.]+)\s*[μµ]?g/m³'
    }
    
    for item in dados_json:
        estado = item.get('estado', '')
        estado_nome = item.get('estado_nome', '')
        data_coleta = item.get('data_coleta', '')
        indicadores = item.get('indicadores', {})
        
        # Buscar o texto completo dos indicadores
        texto_indicadores = None
        for key in indicadores.keys():
            if 'PM' in key and 'μg/m³' in key:
                texto_indicadores = key
                break
        
        if texto_indicadores:
            pm25 = extrair_valor_indicador(texto_indicadores, padroes['PM2.5'])
            pm10 = extrair_valor_indicador(texto_indicadores, padroes['PM10'])
            o3 = extrair_valor_indicador(texto_indicadores, padroes['O3'])
            so2 = extrair_valor_indicador(texto_indicadores, padroes['SO2'])
            no2 = extrair_valor_indicador(texto_indicadores, padroes['NO2'])
            
            registros.append({
                'estado': estado,
                'estado_nome': estado_nome,
                'data_coleta': data_coleta,
                'PM2.5': pm25,
                'PM10': pm10,
                'O3': o3,
                'SO2': so2,
                'NO2': no2
            })
    
    df = pd.DataFrame(registros)
    
    # Calcular AQI
    df['AQI'] = df['PM2.5'].apply(calcular_aqi_pm25)
    df['Categoria'] = df['AQI'].apply(lambda x: obter_categoria_aqi(x)[0])
    df['Cor'] = df['AQI'].apply(lambda x: obter_categoria_aqi(x)[1])
    
    return df

@st.cache_data(ttl=300, show_spinner=False)
def carregar_dados():
    """Carrega dados dos arquivos mais recentes"""
    
    # Procurar arquivos na pasta downloads_inpe
    pasta_downloads = 'downloads_inpe'
    
    if not os.path.exists(pasta_downloads):
        return None
    
    arquivos_semana = glob.glob(os.path.join(pasta_downloads, 'dados_inpe_semana_*.csv'))
    arquivos_hoje_json = glob.glob(os.path.join(pasta_downloads, 'dados_inpe_hoje_*.json'))
    
    dados = {}
    
    # Carregar dados de semana epidemiológica (para série temporal)
    if arquivos_semana:
        arquivo_mais_recente = max(arquivos_semana, key=os.path.getctime)
        try:
            df_semana = pd.read_csv(arquivo_mais_recente)
            # IMPORTANTE: Processar dados para normalizar colunas
            df_semana = processar_dados_semana(df_semana)
            dados['semana'] = df_semana
            dados['arquivo_semana'] = os.path.basename(arquivo_mais_recente)
        except Exception as e:
            st.error(f"Erro ao ler {arquivo_mais_recente}: {e}")
    
    # Carregar dados de hoje (JSON - para visão geral)
    if arquivos_hoje_json:
        arquivo_mais_recente = max(arquivos_hoje_json, key=os.path.getctime)
        try:
            with open(arquivo_mais_recente, 'r', encoding='utf-8') as f:
                dados_json = json.load(f)
            
            df_hoje = processar_dados_hoje(dados_json)
            dados['hoje'] = df_hoje
            dados['arquivo_hoje'] = os.path.basename(arquivo_mais_recente)
        except Exception as e:
            st.error(f"Erro ao ler {arquivo_mais_recente}: {e}")
    
    return dados

def processar_dados_semana(df):
    """Processa dados de semana epidemiológica"""
    df = df.copy()
    
    # Converter data
    if 'date' in df.columns:
        df['data'] = pd.to_datetime(df['date'], errors='coerce')
    
    # Renomear colunas para facilitar
    if 'pm2_5_media_diaria_previsao_situacao_atual' in df.columns:
        df['PM2.5'] = df['pm2_5_media_diaria_previsao_situacao_atual']
    
    if 'pm10_media_diaria_previsao_situacao_atual' in df.columns:
        df['PM10'] = df['pm10_media_diaria_previsao_situacao_atual']
    
    if 'o3_media_diaria_previsao_situacao_atual' in df.columns:
        df['O3'] = df['o3_media_diaria_previsao_situacao_atual']
    
    # Calcular AQI
    df['AQI'] = df['PM2.5'].apply(calcular_aqi_pm25)
    df['Categoria'] = df['AQI'].apply(lambda x: obter_categoria_aqi(x)[0])
    df['Cor'] = df['AQI'].apply(lambda x: obter_categoria_aqi(x)[1])
    
    return df

def main():
    # Cabeçalho
    st.title("🌫️ Monitor de Qualidade do Ar - Brasil")
    st.markdown("**Dados do INPE SISAM - Sistema de Informações Ambientais Integrado à Saúde**")
    
    # Botão para recarregar dados
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🔄 Recarregar", help="Limpar cache e recarregar dados"):
            st.cache_data.clear()
            st.rerun()
    
    # Carregar dados
    with st.spinner("Carregando dados..."):
        dados = carregar_dados()
    
    if not dados:
        st.warning("⚠️ Nenhum arquivo de dados encontrado na pasta `downloads_inpe`.")
        st.info("""
        Execute o script de coleta:
        ```bash
        python3 coletar_inpe_sisam.py
        ```
        """)
        return
    
    # Gerar alertas
    with st.spinner("Analisando alertas..."):
        alertas = gerar_todos_alertas(dados)
    
    # Sidebar
    st.sidebar.header("📊 Informações")
    
    # Informações dos arquivos
    with st.sidebar.expander("📁 Arquivos Carregados"):
        if 'arquivo_hoje' in dados:
            st.text(f"Hoje: {dados['arquivo_hoje']}")
        if 'arquivo_semana' in dados:
            st.text(f"Semana: {dados['arquivo_semana']}")
    
    # Resumo de Alertas na Sidebar
    st.sidebar.header("🚨 Sistema de Alertas")
    
    st.sidebar.info("**Padrão**: Estados\n\nUse o filtro na Tab Alertas para alternar")
    
    # Estatísticas por tipo
    with st.sidebar.expander("📊 Alertas no Sistema", expanded=True):
        st.markdown("**🗺️ Estados:**")
        st.text(f"  Total: {len(alertas['estados'])}")
        alertas_estados_num = len([a for a in alertas['estados'] if a['nivel'] == 'alerta'])
        criticos_estados = len([a for a in alertas['estados'] if a['nivel'] == 'critico'])
        st.text(f"  Críticos: {criticos_estados}")
        st.text(f"  Alertas: {alertas_estados_num}")
        
        st.markdown("**🏙️ Municípios:**")
        st.text(f"  Total: {len(alertas['municipios'])}")
        alertas_munic = len([a for a in alertas['municipios'] if a['nivel'] == 'alerta'])
        criticos_munic = len([a for a in alertas['municipios'] if a['nivel'] == 'critico'])
        st.text(f"  Críticos: {criticos_munic}")
        st.text(f"  Alertas: {alertas_munic}")
    
    # Detalhes
    with st.sidebar.expander("💡 Como Funciona"):
        st.caption("""
        **Sistema de Visualização:**
        
        • Todos os alertas detectados estão disponíveis
        • Visualização paginada (20 por página)
        • Ordenação automática por severidade
        • Filtros: tipo de região, nível, poluente
        
        **Navegação:**
        Use a Tab "Alertas" para visualizar e filtrar todos os alertas do sistema.
        """)
    
    st.sidebar.divider()
    
    # Legenda de níveis de alerta
    with st.sidebar.expander("🎨 Legenda de Alertas"):
        for nivel, info in NIVEIS_ALERTA.items():
            st.markdown(f"{info['icone']} **{info['nome']}** - {nivel.capitalize()}")
    
    # Padrões OMS
    with st.sidebar.expander("ℹ️ Padrões OMS 2021"):
        st.markdown("""
        **PM2.5:**
        - 24h: 15 µg/m³
        - Anual: 5 µg/m³
        
        **PM10:**
        - 24h: 45 µg/m³
        - Anual: 15 µg/m³
        
        **O3:**
        - 8h: 100 µg/m³
        """)
    
    # Tabs principais
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📍 Visão Geral", "🚨 Alertas", "📈 Série Temporal", "🏆 Rankings", "📋 Dados Brutos"])
    
    # TAB 1: Visão Geral
    with tab1:
        if 'hoje' in dados:
            df_hoje = dados['hoje']
            
            # Métricas principais
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_estados = len(df_hoje)
                st.metric("🗺️ Estados", f"{total_estados}")
            
            with col2:
                pm25_medio = df_hoje['PM2.5'].mean()
                delta_oms = pm25_medio - PADROES['PM2.5']['24h']
                st.metric(
                    "💨 PM2.5 Médio", 
                    f"{pm25_medio:.1f} µg/m³",
                    delta=f"{delta_oms:+.1f} vs OMS",
                    delta_color="inverse"
                )
            
            with col3:
                pm10_medio = df_hoje['PM10'].mean()
                delta_oms_pm10 = pm10_medio - PADROES['PM10']['24h']
                st.metric(
                    "🌪️ PM10 Médio", 
                    f"{pm10_medio:.1f} µg/m³",
                    delta=f"{delta_oms_pm10:+.1f} vs OMS",
                    delta_color="inverse"
                )
            
            with col4:
                if 'data_coleta' in df_hoje.columns:
                    data_mais_recente = pd.to_datetime(df_hoje['data_coleta'].iloc[0], errors='coerce')
                    st.metric("📅 Última Coleta", 
                             data_mais_recente.strftime("%d/%m/%Y %H:%M") if pd.notna(data_mais_recente) else "Hoje")
            
            st.divider()
            
            # Seção de Alertas do Dia
            st.subheader("🚨 Alertas do Dia - Estados com Pior Qualidade do Ar")
            
            st.caption("📊 Exibindo estados com concentrações acima dos limites OMS")
            
            alertas_estados = [a for a in alertas['estados'] if a['nivel'] in ['critico', 'alerta']]
            
            if len(alertas_estados) > 0:
                # Alertas críticos em destaque
                alertas_criticos = [a for a in alertas_estados if a['nivel'] == 'critico']
                if alertas_criticos:
                    st.markdown("**🔴 Nível Crítico (PM2.5 > 35 µg/m³):**")
                    for alerta in alertas_criticos[:3]:  # Mostrar top 3
                        st.error(f"{alerta['icone']} **{alerta['regiao']}** - {alerta['mensagem']}")
                
                # Outros alertas
                outros_alertas = [a for a in alertas_estados if a['nivel'] == 'alerta']
                if outros_alertas:
                    st.markdown("**🟠 Alerta OMS (PM2.5 > 15 µg/m³):**")
                    with st.expander(f"⚠️ Ver todos os alertas ({len(outros_alertas)} estados)", expanded=True):
                        for alerta in outros_alertas:
                            st.warning(f"{alerta['icone']} **{alerta['regiao']}** - {alerta['mensagem']}")
            else:
                st.success("✅ Nenhum alerta crítico no momento. Qualidade do ar em níveis aceitáveis na maioria dos estados.")
            
            # Melhorias
            melhorias = [a for a in alertas['estados'] if a['nivel'] == 'melhoria']
            if melhorias:
                with st.expander(f"✅ Melhorias detectadas ({len(melhorias)})", expanded=False):
                    for alerta in melhorias:
                        st.success(f"{alerta['icone']} **{alerta['regiao']}** - {alerta['mensagem']}")
            
            st.divider()
            
            # Gráfico de barras por estado
            st.subheader("🗺️ Concentração de PM2.5 por Estado (Hoje)")
            
            df_estados = df_hoje[['estado_nome', 'PM2.5', 'PM10', 'O3']].copy()
            df_estados.columns = ['Estado', 'PM2.5', 'PM10', 'O3']
            
            # Adicionar indicador de alerta
            estados_com_alerta = {a['regiao']: a['icone'] for a in alertas_estados}
            df_estados['Alerta'] = df_estados['Estado'].map(estados_com_alerta).fillna('')
            df_estados['Estado_Label'] = df_estados['Estado'] + ' ' + df_estados['Alerta']
            
            df_estados = df_estados.sort_values('PM2.5', ascending=False)
            
            fig_estados = px.bar(
                df_estados,
                x='PM2.5',
                y='Estado_Label',
                orientation='h',
                title='Todos os Estados - PM2.5 Atual (com indicadores de alerta)',
                labels={'PM2.5': 'PM2.5 (µg/m³)', 'Estado_Label': 'Estado'},
                color='PM2.5',
                color_continuous_scale='Reds',
                hover_data={'PM10': ':.2f', 'O3': ':.2f', 'Estado_Label': False, 'Estado': True}
            )
            fig_estados.add_vline(
                x=15, 
                line_dash="dash", 
                line_color="orange",
                annotation_text="Limite OMS (15 µg/m³)",
                annotation_position="top"
            )
            fig_estados.update_layout(height=500)
            
            st.plotly_chart(fig_estados, use_container_width=True)
            
            # Distribuição de qualidade do ar
            st.subheader("📊 Distribuição de Categorias de Qualidade do Ar (Hoje)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de pizza - categorias
                df_categorias = df_hoje['Categoria'].value_counts().reset_index()
                df_categorias.columns = ['Categoria', 'Count']
                
                fig_pizza = px.pie(
                    df_categorias,
                    values='Count',
                    names='Categoria',
                    title='Distribuição de Categorias (AQI)',
                    color='Categoria',
                    color_discrete_map={
                        'Boa': '#00E400',
                        'Moderada': '#FFFF00',
                        'Insalubre p/ Sensíveis': '#FF7E00',
                        'Insalubre': '#FF0000',
                        'Muito Insalubre': '#8F3F97',
                        'Perigosa': '#7E0023'
                    }
                )
                st.plotly_chart(fig_pizza, use_container_width=True)
            
            with col2:
                # Gráfico de barras comparativo dos 3 poluentes
                df_poluentes = pd.DataFrame({
                    'Poluente': ['PM2.5', 'PM10', 'O3'],
                    'Concentração Média': [
                        df_hoje['PM2.5'].mean(),
                        df_hoje['PM10'].mean(),
                        df_hoje['O3'].mean()
                    ],
                    'Limite OMS': [15, 45, 100]
                })
                
                fig_comparacao = go.Figure()
                fig_comparacao.add_trace(go.Bar(
                    name='Média Brasil',
                    x=df_poluentes['Poluente'],
                    y=df_poluentes['Concentração Média'],
                    marker_color='lightblue'
                ))
                fig_comparacao.add_trace(go.Bar(
                    name='Limite OMS',
                    x=df_poluentes['Poluente'],
                    y=df_poluentes['Limite OMS'],
                    marker_color='red',
                    opacity=0.5
                ))
                fig_comparacao.update_layout(
                    title='Concentração Média vs Limite OMS',
                    yaxis_title='µg/m³',
                    barmode='group',
                    height=400
                )
                st.plotly_chart(fig_comparacao, use_container_width=True)
            
            # Estatísticas gerais
            st.subheader("📊 Estatísticas por Estado (Hoje)")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("### PM2.5")
                acima_oms = (df_hoje['PM2.5'] > PADROES['PM2.5']['24h']).sum()
                total = len(df_hoje)
                pct_acima = (acima_oms / total * 100) if total > 0 else 0
                
                st.metric("Estados acima do limite", f"{acima_oms}")
                st.metric("Percentual", f"{pct_acima:.1f}%")
                st.metric("Máximo", f"{df_hoje['PM2.5'].max():.1f} µg/m³")
                st.metric("Mínimo", f"{df_hoje['PM2.5'].min():.1f} µg/m³")
            
            with col2:
                st.markdown("### PM10")
                acima_oms_pm10 = (df_hoje['PM10'] > PADROES['PM10']['24h']).sum()
                pct_acima_pm10 = (acima_oms_pm10 / total * 100) if total > 0 else 0
                
                st.metric("Estados acima do limite", f"{acima_oms_pm10}")
                st.metric("Percentual", f"{pct_acima_pm10:.1f}%")
                st.metric("Máximo", f"{df_hoje['PM10'].max():.1f} µg/m³")
                st.metric("Mínimo", f"{df_hoje['PM10'].min():.1f} µg/m³")
            
            with col3:
                st.markdown("### O3 (Ozônio)")
                acima_oms_o3 = (df_hoje['O3'] > PADROES['O3']['8h']).sum()
                pct_acima_o3 = (acima_oms_o3 / total * 100) if total > 0 else 0
                
                st.metric("Estados acima do limite", f"{acima_oms_o3}")
                st.metric("Percentual", f"{pct_acima_o3:.1f}%")
                st.metric("Máximo", f"{df_hoje['O3'].max():.1f} µg/m³")
                st.metric("Mínimo", f"{df_hoje['O3'].min():.1f} µg/m³")
    
    # TAB 2: Alertas
    with tab2:
        st.header("🚨 Sistema de Alertas de Qualidade do Ar")
        
        st.info("""
        **📊 Critério de Exibição: TOP 20 PIORES CASOS**
        
        Este painel mostra os **20 alertas mais críticos** do Brasil, selecionados por:
        1. **Prioridade do nível** (Crítico > Alerta > Aviso > Melhoria)
        2. **Maior concentração** de poluentes (valores mais altos primeiro)
        
        **Tipos de alertas detectados:**
        - 🔴 **Níveis Críticos**: Valores acima dos limites críticos de saúde (PM2.5 > 35 µg/m³)
        - 🟠 **Alertas OMS**: Valores acima dos padrões recomendados pela OMS (PM2.5 > 15 µg/m³)
        - 🟡 **Mudanças Bruscas**: Variações significativas vs média histórica
        - 🟢 **Melhorias**: Retorno aos níveis aceitáveis
        """)
        
        # Filtros primeiro (para definir o contexto)
        st.markdown("### 🔍 Filtros de Visualização")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filtro_tipo_regiao = st.selectbox(
                "📍 Tipo de Região:",
                options=['Estados', 'Municípios'],
                index=0,  # Estados como padrão
                help="Selecione o tipo de região para filtrar os alertas",
                key='filtro_tipo_regiao'
            )
        
        with col2:
            filtro_nivel = st.multiselect(
                "🎚️ Filtrar por Nível:",
                options=['critico', 'alerta', 'aviso', 'melhoria'],
                default=['critico', 'alerta', 'aviso', 'melhoria'],
                format_func=lambda x: NIVEIS_ALERTA[x]['nome'],
                key='filtro_nivel'
            )
        
        with col3:
            filtro_poluente = st.multiselect(
                "🧪 Filtrar por Poluente:",
                options=['PM2.5', 'PM10', 'O3'],
                default=['PM2.5', 'PM10', 'O3'],
                key='filtro_poluente'
            )
        
        # Detectar mudança nos filtros e resetar página
        filtros_atuais = f"{filtro_tipo_regiao}_{filtro_nivel}_{filtro_poluente}"
        if 'filtros_anteriores' not in st.session_state:
            st.session_state.filtros_anteriores = filtros_atuais
        
        if st.session_state.filtros_anteriores != filtros_atuais:
            st.session_state.pagina_alertas = 1
            st.session_state.filtros_anteriores = filtros_atuais
        
        # Aplicar filtros
        alertas_filtrados = alertas['todos'].copy()
        
        # Filtro de tipo de região (sempre aplicado)
        tipo_map = {'Estados': 'estado', 'Municípios': 'municipio'}
        alertas_filtrados = [a for a in alertas_filtrados if a['regiao_tipo'] == tipo_map[filtro_tipo_regiao]]
        
        # Filtro de nível
        if filtro_nivel:
            alertas_filtrados = [a for a in alertas_filtrados if a['nivel'] in filtro_nivel]
        
        # Filtro de poluente
        if filtro_poluente:
            alertas_filtrados = [a for a in alertas_filtrados if a['poluente'] in filtro_poluente]
        
        # Recalcular estatísticas baseadas nos alertas filtrados
        stats_filtradas = {
            'total': len(alertas_filtrados),
            'criticos': len([a for a in alertas_filtrados if a['nivel'] == 'critico']),
            'alertas': len([a for a in alertas_filtrados if a['nivel'] == 'alerta']),
            'avisos': len([a for a in alertas_filtrados if a['nivel'] == 'aviso']),
            'melhorias': len([a for a in alertas_filtrados if a['nivel'] == 'melhoria'])
        }
        
        st.divider()
        
        # Estatísticas dos alertas filtrados
        st.markdown(f"### 📊 Estatísticas - {filtro_tipo_regiao}")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "🚨 Críticos",
                stats_filtradas['criticos'],
                help=f"Alertas críticos em {filtro_tipo_regiao.lower()}"
            )
        
        with col2:
            st.metric(
                "⚠️ Alertas",
                stats_filtradas['alertas'],
                help=f"Alertas OMS em {filtro_tipo_regiao.lower()}"
            )
        
        with col3:
            st.metric(
                "⚡ Avisos",
                stats_filtradas['avisos'],
                help=f"Avisos em {filtro_tipo_regiao.lower()}"
            )
        
        with col4:
            st.metric(
                "✅ Melhorias",
                stats_filtradas['melhorias'],
                help=f"Melhorias em {filtro_tipo_regiao.lower()}"
            )
        
        st.divider()
        
        # Mostrar alertas em cards com paginação
        if len(alertas_filtrados) > 0:
            # Configuração de paginação
            alertas_por_pagina = 20
            total_alertas = len(alertas_filtrados)
            total_paginas = (total_alertas + alertas_por_pagina - 1) // alertas_por_pagina
            
            # Inicializar página no session_state
            if 'pagina_alertas' not in st.session_state:
                st.session_state.pagina_alertas = 1
            
            # Garantir que a página está dentro dos limites
            if st.session_state.pagina_alertas > total_paginas:
                st.session_state.pagina_alertas = 1
            
            # Calcular índices
            inicio = (st.session_state.pagina_alertas - 1) * alertas_por_pagina
            fim = min(inicio + alertas_por_pagina, total_alertas)
            
            # Mensagem explicativa
            st.info(f"""
            **📊 Exibindo {total_alertas} alertas de {filtro_tipo_regiao}**
            
            **Ordenação:**
            - Prioridade 1️⃣: Nível de severidade (Crítico → Alerta → Aviso → Melhoria)
            - Prioridade 2️⃣: Maior concentração de poluentes (piores valores primeiro)
            
            💡 **Navegação**: Use os botões abaixo para navegar entre as páginas.
            """)
            
            # Controles de paginação (superior)
            col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
            
            with col1:
                if st.button("⏮️ Primeira", disabled=(st.session_state.pagina_alertas == 1)):
                    st.session_state.pagina_alertas = 1
                    st.rerun()
            
            with col2:
                if st.button("◀️ Anterior", disabled=(st.session_state.pagina_alertas == 1)):
                    st.session_state.pagina_alertas -= 1
                    st.rerun()
            
            with col3:
                st.markdown(f"<div style='text-align: center; padding: 8px;'><b>Página {st.session_state.pagina_alertas} de {total_paginas}</b><br/><small>Alertas {inicio + 1}-{fim} de {total_alertas}</small></div>", unsafe_allow_html=True)
            
            with col4:
                if st.button("Próxima ▶️", disabled=(st.session_state.pagina_alertas == total_paginas)):
                    st.session_state.pagina_alertas += 1
                    st.rerun()
            
            with col5:
                if st.button("Última ⏭️", disabled=(st.session_state.pagina_alertas == total_paginas)):
                    st.session_state.pagina_alertas = total_paginas
                    st.rerun()
            
            st.divider()
            
            # Mostrar alertas da página atual
            for i, alerta in enumerate(alertas_filtrados[inicio:fim]):
                # Cor do card baseado no nível
                if alerta['nivel'] == 'critico':
                    card_type = 'error'
                elif alerta['nivel'] == 'alerta':
                    card_type = 'warning'
                elif alerta['nivel'] == 'melhoria':
                    card_type = 'success'
                else:
                    card_type = 'info'
                
                with st.expander(
                    f"{alerta['icone']} [{alerta['nome_nivel']}] {alerta['regiao']} - {alerta['poluente']}",
                    expanded=(i < 3 and alerta['nivel'] == 'critico')  # Expandir primeiros 3 críticos
                ):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**Mensagem:** {alerta['mensagem']}")
                        st.markdown(f"**Tipo:** {alerta['tipo'].replace('_', ' ').title()}")
                        st.markdown(f"**Região:** {alerta['regiao']} ({alerta['regiao_tipo']})")
                        
                        if alerta['variacao_pct']:
                            st.markdown(f"**Variação:** {alerta['variacao_pct']:+.1f}%")
                    
                    with col2:
                        st.markdown(f"**Valor Atual:**")
                        st.markdown(f"# {alerta['valor_atual']:.1f}")
                        st.markdown("µg/m³")
                        
                        if alerta['valor_referencia']:
                            st.markdown(f"**Referência:** {alerta['valor_referencia']:.1f} µg/m³")
                    
                    # Recomendações de saúde
                    if alerta['recomendacao']:
                        st.markdown("---")
                        st.markdown("**🏥 Recomendações de Saúde:**")
                        st.markdown(alerta['recomendacao'])
                    
                    # Categoria AQI
                    if alerta['categoria_aqi']:
                        st.markdown(f"**Categoria AQI:** {alerta['categoria_aqi']}")
            
            # Controles de paginação (inferior)
            st.divider()
            col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
            
            with col1:
                if st.button("⏮️ Primeira ", key="primeira_bottom", disabled=(st.session_state.pagina_alertas == 1)):
                    st.session_state.pagina_alertas = 1
                    st.rerun()
            
            with col2:
                if st.button("◀️ Anterior ", key="anterior_bottom", disabled=(st.session_state.pagina_alertas == 1)):
                    st.session_state.pagina_alertas -= 1
                    st.rerun()
            
            with col3:
                st.markdown(f"<div style='text-align: center; padding: 8px;'><b>Página {st.session_state.pagina_alertas} de {total_paginas}</b></div>", unsafe_allow_html=True)
            
            with col4:
                if st.button("Próxima ▶️ ", key="proxima_bottom", disabled=(st.session_state.pagina_alertas == total_paginas)):
                    st.session_state.pagina_alertas += 1
                    st.rerun()
            
            with col5:
                if st.button("Última ⏭️ ", key="ultima_bottom", disabled=(st.session_state.pagina_alertas == total_paginas)):
                    st.session_state.pagina_alertas = total_paginas
                    st.rerun()
        else:
            st.success("✅ Nenhum alerta encontrado com os filtros selecionados.")
        
        # Distribuição de alertas por tipo
        if len(alertas_filtrados) > 0:
            st.divider()
            st.subheader("📊 Distribuição de Alertas")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Por nível
                df_nivel = pd.DataFrame([
                    {'Nível': NIVEIS_ALERTA[a['nivel']]['nome'], 'Quantidade': 1}
                    for a in alertas_filtrados
                ])
                df_nivel = df_nivel.groupby('Nível').sum().reset_index()
                
                fig_nivel = px.pie(
                    df_nivel,
                    values='Quantidade',
                    names='Nível',
                    title='Alertas por Nível',
                    color='Nível',
                    color_discrete_map={
                        'CRÍTICO': '#FF0000',
                        'ALERTA': '#FF7E00',
                        'AVISO': '#FFFF00',
                        'MELHORIA': '#00E400'
                    }
                )
                st.plotly_chart(fig_nivel, use_container_width=True)
            
            with col2:
                # Por poluente
                df_poluente = pd.DataFrame([
                    {'Poluente': a['poluente'], 'Quantidade': 1}
                    for a in alertas_filtrados
                ])
                df_poluente = df_poluente.groupby('Poluente').sum().reset_index()
                
                fig_poluente = px.bar(
                    df_poluente,
                    x='Poluente',
                    y='Quantidade',
                    title='Alertas por Poluente',
                    color='Poluente',
                    color_discrete_sequence=['#636EFA', '#EF553B', '#00CC96']
                )
                st.plotly_chart(fig_poluente, use_container_width=True)
    
    # TAB 3: Série Temporal
    with tab3:
        st.subheader("📈 Evolução Temporal dos Poluentes")
        
        if 'semana' in dados:
            df_semana = processar_dados_semana(dados['semana'])
            
            # Mostrar alertas de municípios
            if len(alertas['municipios']) > 0:
                with st.expander(f"⚠️ Municípios em Situação Crítica ({len(alertas['municipios'])})", expanded=True):
                    for alerta in alertas['municipios'][:10]:  # Top 10
                        if alerta['nivel'] == 'critico':
                            st.error(f"{alerta['icone']} {alerta['regiao']} - {alerta['mensagem']}")
                        else:
                            st.warning(f"{alerta['icone']} {alerta['regiao']} - {alerta['mensagem']}")
                st.divider()
            
            # Filtros
            col1, col2, col3 = st.columns(3)
            
            with col1:
                estados_disponiveis = ['Todos'] + sorted(df_semana['estado'].unique().tolist())
                estado_selecionado = st.selectbox("Estado:", estados_disponiveis)
            
            with col2:
                if estado_selecionado != 'Todos':
                    df_filtrado = df_semana[df_semana['estado'] == estado_selecionado]
                    municipios_disponiveis = ['Todos'] + sorted(df_filtrado['municipio'].unique().tolist())
                else:
                    df_filtrado = df_semana
                    municipios_disponiveis = ['Todos']
                
                municipio_selecionado = st.selectbox("Município:", municipios_disponiveis)
            
            with col3:
                filtrar_alertas = st.checkbox("Mostrar apenas municípios com alertas", value=False)
            
            # Aplicar filtros
            if estado_selecionado != 'Todos':
                df_plot = df_semana[df_semana['estado'] == estado_selecionado].copy()
                
                if municipio_selecionado != 'Todos':
                    df_plot = df_plot[df_plot['municipio'] == municipio_selecionado].copy()
            else:
                df_plot = df_semana.copy()
            
            # Filtrar apenas municípios com alertas
            if filtrar_alertas and len(alertas['municipios']) > 0:
                municipios_com_alerta = [a['regiao'] for a in alertas['municipios']]
                if 'municipio' in df_plot.columns and 'estado' in df_plot.columns:
                    df_plot['regiao_completa'] = df_plot['municipio'] + '/' + df_plot['estado']
                    df_plot = df_plot[df_plot['regiao_completa'].isin(municipios_com_alerta)].copy()
                    df_plot = df_plot.drop('regiao_completa', axis=1)
            
            if 'data' in df_plot.columns and len(df_plot) > 0:
                # Agrupar por data
                df_temporal = df_plot.groupby('data').agg({
                    'PM2.5': 'mean',
                    'PM10': 'mean',
                    'O3': 'mean'
                }).reset_index()
                
                df_temporal = df_temporal.sort_values('data')
                
                # Gráfico de linha
                fig_temporal = go.Figure()
                
                fig_temporal.add_trace(go.Scatter(
                    x=df_temporal['data'],
                    y=df_temporal['PM2.5'],
                    name='PM2.5',
                    mode='lines+markers',
                    line=dict(color='#636EFA', width=2),
                    marker=dict(size=6)
                ))
                
                fig_temporal.add_trace(go.Scatter(
                    x=df_temporal['data'],
                    y=df_temporal['PM10'],
                    name='PM10',
                    mode='lines+markers',
                    line=dict(color='#EF553B', width=2),
                    marker=dict(size=6)
                ))
                
                fig_temporal.add_trace(go.Scatter(
                    x=df_temporal['data'],
                    y=df_temporal['O3'],
                    name='O3',
                    mode='lines+markers',
                    line=dict(color='#00CC96', width=2),
                    marker=dict(size=6)
                ))
                
                # Linhas de referência OMS
                fig_temporal.add_hline(
                    y=15, 
                    line_dash="dash", 
                    line_color="orange",
                    annotation_text="PM2.5 - OMS",
                    annotation_position="right"
                )
                
                fig_temporal.add_hline(
                    y=45, 
                    line_dash="dash", 
                    line_color="red",
                    annotation_text="PM10 - OMS",
                    annotation_position="right"
                )
                
                titulo = f'Evolução Temporal'
                if estado_selecionado != 'Todos':
                    titulo += f' - {estado_selecionado}'
                if municipio_selecionado != 'Todos':
                    titulo += f' - {municipio_selecionado}'
                
                fig_temporal.update_layout(
                    title=titulo,
                    xaxis_title='Data',
                    yaxis_title='Concentração (µg/m³)',
                    hovermode='x unified',
                    height=500,
                    showlegend=True
                )
                
                st.plotly_chart(fig_temporal, use_container_width=True)
                
                # Estatísticas do período
                st.subheader("📊 Estatísticas do Período Selecionado")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("#### PM2.5")
                    st.metric("Mínimo", f"{df_temporal['PM2.5'].min():.1f} µg/m³")
                    st.metric("Médio", f"{df_temporal['PM2.5'].mean():.1f} µg/m³")
                    st.metric("Máximo", f"{df_temporal['PM2.5'].max():.1f} µg/m³")
                
                with col2:
                    st.markdown("#### PM10")
                    st.metric("Mínimo", f"{df_temporal['PM10'].min():.1f} µg/m³")
                    st.metric("Médio", f"{df_temporal['PM10'].mean():.1f} µg/m³")
                    st.metric("Máximo", f"{df_temporal['PM10'].max():.1f} µg/m³")
                
                with col3:
                    st.markdown("#### O3")
                    st.metric("Mínimo", f"{df_temporal['O3'].min():.1f} µg/m³")
                    st.metric("Médio", f"{df_temporal['O3'].mean():.1f} µg/m³")
                    st.metric("Máximo", f"{df_temporal['O3'].max():.1f} µg/m³")
    
    # TAB 4: Rankings
    with tab4:
        st.subheader("🏆 Rankings de Municípios")
        
        if 'semana' in dados:
            df_semana = processar_dados_semana(dados['semana'])
            
            # Seção de municípios em situação crítica
            if len(alertas['municipios']) > 0:
                st.markdown("### 🔥 Municípios em Situação Crítica")
                
                df_alertas_criticos = pd.DataFrame([
                    {
                        'Ícone': a['icone'],
                        'Município': a['regiao'].split('/')[0],
                        'UF': a['regiao'].split('/')[1] if '/' in a['regiao'] else '',
                        'Poluente': a['poluente'],
                        'Valor': f"{a['valor_atual']:.1f}",
                        'Nível': a['nome_nivel']
                    }
                    for a in alertas['municipios'][:15]  # Top 15
                ])
                
                st.dataframe(df_alertas_criticos, hide_index=True, use_container_width=True)
                st.divider()
            
            # Calcular médias por município
            df_ranking = df_semana.groupby(['municipio', 'estado']).agg({
                'PM2.5': 'mean',
                'PM10': 'mean',
                'O3': 'mean',
                'AQI': 'mean'
            }).reset_index()
            
            # Adicionar indicador de alerta ao ranking
            df_ranking['regiao_completa'] = df_ranking['municipio'] + '/' + df_ranking['estado']
            municipios_alertas = {a['regiao']: a['icone'] for a in alertas['municipios']}
            df_ranking['Alerta'] = df_ranking['regiao_completa'].map(municipios_alertas).fillna('')
            df_ranking = df_ranking.drop('regiao_completa', axis=1)
            
            # Seletor de poluente
            poluente_ranking = st.selectbox(
                "Selecione o poluente para ranking:",
                ['PM2.5', 'PM10', 'O3', 'AQI']
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"### ✅ Top 10 Melhor Qualidade ({poluente_ranking})")
                df_melhores = df_ranking.nsmallest(10, poluente_ranking).copy()
                df_melhores['Posição'] = range(1, len(df_melhores) + 1)
                df_melhores_display = df_melhores[['Posição', 'Alerta', 'municipio', 'estado', poluente_ranking]]
                df_melhores_display.columns = ['🏅', '⚠️', 'Município', 'UF', poluente_ranking]
                st.dataframe(df_melhores_display, hide_index=True, use_container_width=True)
            
            with col2:
                st.markdown(f"### ⚠️ Top 10 Pior Qualidade ({poluente_ranking})")
                df_piores = df_ranking.nlargest(10, poluente_ranking).copy()
                df_piores['Posição'] = range(1, len(df_piores) + 1)
                df_piores_display = df_piores[['Posição', 'Alerta', 'municipio', 'estado', poluente_ranking]]
                df_piores_display.columns = ['⚠️', '🚨', 'Município', 'UF', poluente_ranking]
                st.dataframe(df_piores_display, hide_index=True, use_container_width=True)
            
            st.divider()
            
            # Gráfico comparativo
            st.subheader(f"📊 Comparação - {poluente_ranking}")
            
            df_comparacao = pd.concat([
                df_melhores.head(10).assign(Grupo='Melhor'),
                df_piores.head(10).assign(Grupo='Pior')
            ])
            
            fig_comparacao = px.bar(
                df_comparacao,
                x=poluente_ranking,
                y='municipio',
                color='Grupo',
                orientation='h',
                title=f'{poluente_ranking} - Comparação Top 10 Melhores vs Piores',
                labels={poluente_ranking: f'{poluente_ranking} (µg/m³)', 'municipio': 'Município'},
                color_discrete_map={'Melhor': 'lightgreen', 'Pior': 'lightcoral'},
                hover_data=['estado']
            )
            
            # Adicionar linha de referência OMS
            if poluente_ranking in PADROES:
                limite = PADROES[poluente_ranking].get('24h') or PADROES[poluente_ranking].get('8h')
                if limite:
                    fig_comparacao.add_vline(
                        x=limite,
                        line_dash="dash",
                        line_color="red",
                        annotation_text=f"Limite OMS ({limite})"
                    )
            
            fig_comparacao.update_layout(height=600)
            st.plotly_chart(fig_comparacao, use_container_width=True)
    
    # TAB 5: Dados Brutos
    with tab5:
        st.subheader("📋 Dados Brutos")
        
        if 'semana' in dados:
            df_semana = processar_dados_semana(dados['semana'])
            
            # Adicionar coluna de alerta
            df_semana['regiao_completa'] = df_semana['municipio'] + '/' + df_semana['estado']
            municipios_alertas = {a['regiao']: a['icone'] for a in alertas['municipios']}
            df_semana['Alerta'] = df_semana['regiao_completa'].map(municipios_alertas).fillna('')
            df_semana = df_semana.drop('regiao_completa', axis=1)
            
            st.info(f"📄 {len(df_semana):,} registros | 📊 {len(df_semana.columns)} colunas | 🏙️ {df_semana['municipio'].nunique():,} municípios | 🚨 {len(alertas['municipios'])} com alertas")
            
            # Filtros
            col1, col2, col3 = st.columns(3)
            
            with col1:
                estados_filtro = st.multiselect(
                    "Filtrar por Estado:",
                    options=sorted(df_semana['estado'].unique().tolist()),
                    default=[]
                )
            
            with col2:
                categorias_filtro = st.multiselect(
                    "Filtrar por Categoria:",
                    options=sorted(df_semana['Categoria'].unique().tolist()),
                    default=[]
                )
            
            with col3:
                alerta_filtro = st.selectbox(
                    "Filtrar por Alerta:",
                    options=['Todos', 'Apenas com alerta', 'Sem alerta']
                )
            
            # Aplicar filtros
            df_mostrar = df_semana.copy()
            
            if estados_filtro:
                df_mostrar = df_mostrar[df_mostrar['estado'].isin(estados_filtro)]
            
            if categorias_filtro:
                df_mostrar = df_mostrar[df_mostrar['Categoria'].isin(categorias_filtro)]
            
            if alerta_filtro == 'Apenas com alerta':
                df_mostrar = df_mostrar[df_mostrar['Alerta'] != '']
            elif alerta_filtro == 'Sem alerta':
                df_mostrar = df_mostrar[df_mostrar['Alerta'] == '']
            
            # Mostrar dados
            st.dataframe(
                df_mostrar[['Alerta', 'data', 'estado', 'municipio', 'PM2.5', 'PM10', 'O3', 'AQI', 'Categoria']],
                use_container_width=True,
                height=500
            )
            
            # Botões de download
            col1, col2 = st.columns(2)
            
            with col1:
                csv = df_mostrar.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⬇️ Baixar Dados Filtrados (CSV)",
                    data=csv,
                    file_name=f'dados_qualidade_ar_filtrados_{datetime.now().strftime("%Y%m%d")}.csv',
                    mime='text/csv'
                )
            
            with col2:
                csv_completo = df_semana.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⬇️ Baixar Dados Completos (CSV)",
                    data=csv_completo,
                    file_name=f'dados_qualidade_ar_completo_{datetime.now().strftime("%Y%m%d")}.csv',
                    mime='text/csv'
                )
    
    # Rodapé
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <small>
        📊 <b>Dados:</b> INPE SISAM | 
        🔄 <b>Atualização:</b> Automática | 
        💻 <b>Monitor de Qualidade do Ar - Brasil</b><br>
        🌍 Padrões baseados na OMS 2021 | 
        ⚠️ Dados para fins informativos
        </small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

