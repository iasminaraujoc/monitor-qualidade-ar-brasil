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

@st.cache_data(ttl=300)
def carregar_dados():
    """Carrega dados dos CSVs mais recentes"""
    
    # Procurar arquivos CSV na pasta downloads_inpe
    pasta_downloads = 'downloads_inpe'
    
    if not os.path.exists(pasta_downloads):
        return None
    
    arquivos_semana = glob.glob(os.path.join(pasta_downloads, 'dados_inpe_semana_*.csv'))
    arquivos_hoje = glob.glob(os.path.join(pasta_downloads, 'dados_inpe_hoje_*.csv'))
    
    dados = {}
    
    # Carregar dados de semana epidemiológica
    if arquivos_semana:
        arquivo_mais_recente = max(arquivos_semana, key=os.path.getctime)
        try:
            df_semana = pd.read_csv(arquivo_mais_recente)
            dados['semana'] = df_semana
            dados['arquivo_semana'] = os.path.basename(arquivo_mais_recente)
        except Exception as e:
            st.error(f"Erro ao ler {arquivo_mais_recente}: {e}")
    
    # Carregar dados de hoje
    if arquivos_hoje:
        arquivo_mais_recente = max(arquivos_hoje, key=os.path.getctime)
        try:
            df_hoje = pd.read_csv(arquivo_mais_recente)
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
    
    # Sidebar
    st.sidebar.header("📊 Informações")
    
    # Informações dos arquivos
    with st.sidebar.expander("📁 Arquivos Carregados"):
        if 'arquivo_hoje' in dados:
            st.text(f"Hoje: {dados['arquivo_hoje']}")
        if 'arquivo_semana' in dados:
            st.text(f"Semana: {dados['arquivo_semana']}")
    
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
    tab1, tab2, tab3, tab4 = st.tabs(["📍 Visão Geral", "📈 Série Temporal", "🏆 Rankings", "📋 Dados Brutos"])
    
    # TAB 1: Visão Geral
    with tab1:
        if 'semana' in dados:
            df_semana = processar_dados_semana(dados['semana'])
            
            # Métricas principais
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_municipios = df_semana['municipio'].nunique()
                st.metric("🏙️ Municípios", f"{total_municipios:,}")
            
            with col2:
                pm25_medio = df_semana['PM2.5'].mean()
                delta_oms = pm25_medio - PADROES['PM2.5']['24h']
                st.metric(
                    "💨 PM2.5 Médio", 
                    f"{pm25_medio:.1f} µg/m³",
                    delta=f"{delta_oms:+.1f} vs OMS",
                    delta_color="inverse"
                )
            
            with col3:
                pm10_medio = df_semana['PM10'].mean()
                delta_oms_pm10 = pm10_medio - PADROES['PM10']['24h']
                st.metric(
                    "🌪️ PM10 Médio", 
                    f"{pm10_medio:.1f} µg/m³",
                    delta=f"{delta_oms_pm10:+.1f} vs OMS",
                    delta_color="inverse"
                )
            
            with col4:
                if 'data' in df_semana.columns:
                    data_mais_recente = df_semana['data'].max()
                    st.metric("📅 Última Medição", 
                             data_mais_recente.strftime("%d/%m/%Y") if pd.notna(data_mais_recente) else "N/A")
            
            st.divider()
            
            # Gráfico de barras por estado
            st.subheader("🗺️ Concentração Média de PM2.5 por Estado")
            
            df_estados = df_semana.groupby('estado').agg({
                'PM2.5': 'mean',
                'PM10': 'mean',
                'municipio': 'count'
            }).reset_index()
            df_estados.columns = ['Estado', 'PM2.5', 'PM10', 'Municípios']
            df_estados = df_estados.sort_values('PM2.5', ascending=False)
            
            fig_estados = px.bar(
                df_estados.head(15),
                x='PM2.5',
                y='Estado',
                orientation='h',
                title='Top 15 Estados - PM2.5 Médio',
                labels={'PM2.5': 'PM2.5 (µg/m³)', 'Estado': 'Estado'},
                color='PM2.5',
                color_continuous_scale='Reds',
                hover_data={'Municípios': True}
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
            st.subheader("📊 Distribuição de Categorias de Qualidade do Ar")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de pizza - categorias
                df_categorias = df_semana['Categoria'].value_counts().reset_index()
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
                # Histograma PM2.5
                fig_hist = px.histogram(
                    df_semana,
                    x='PM2.5',
                    nbins=50,
                    title='Distribuição de Concentração de PM2.5',
                    labels={'PM2.5': 'PM2.5 (µg/m³)'},
                    color_discrete_sequence=['#636EFA']
                )
                fig_hist.add_vline(
                    x=15, 
                    line_dash="dash", 
                    line_color="red",
                    annotation_text="OMS 24h"
                )
                fig_hist.add_vline(
                    x=35,
                    line_dash="dash",
                    line_color="darkred",
                    annotation_text="Crítico"
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            
            # Estatísticas gerais
            st.subheader("📊 Estatísticas Gerais")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("### PM2.5")
                acima_oms = (df_semana['PM2.5'] > PADROES['PM2.5']['24h']).sum()
                total = len(df_semana)
                pct_acima = (acima_oms / total * 100) if total > 0 else 0
                
                st.metric("Acima do limite OMS", f"{acima_oms:,}")
                st.metric("Percentual", f"{pct_acima:.1f}%")
                st.metric("Máximo registrado", f"{df_semana['PM2.5'].max():.1f} µg/m³")
            
            with col2:
                st.markdown("### PM10")
                acima_oms_pm10 = (df_semana['PM10'] > PADROES['PM10']['24h']).sum()
                pct_acima_pm10 = (acima_oms_pm10 / total * 100) if total > 0 else 0
                
                st.metric("Acima do limite OMS", f"{acima_oms_pm10:,}")
                st.metric("Percentual", f"{pct_acima_pm10:.1f}%")
                st.metric("Máximo registrado", f"{df_semana['PM10'].max():.1f} µg/m³")
            
            with col3:
                st.markdown("### O3 (Ozônio)")
                acima_oms_o3 = (df_semana['O3'] > PADROES['O3']['8h']).sum()
                pct_acima_o3 = (acima_oms_o3 / total * 100) if total > 0 else 0
                
                st.metric("Acima do limite OMS", f"{acima_oms_o3:,}")
                st.metric("Percentual", f"{pct_acima_o3:.1f}%")
                st.metric("Máximo registrado", f"{df_semana['O3'].max():.1f} µg/m³")
    
    # TAB 2: Série Temporal
    with tab2:
        st.subheader("📈 Evolução Temporal dos Poluentes")
        
        if 'semana' in dados:
            df_semana = processar_dados_semana(dados['semana'])
            
            # Filtros
            col1, col2 = st.columns(2)
            
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
            
            # Aplicar filtros
            if estado_selecionado != 'Todos':
                df_plot = df_semana[df_semana['estado'] == estado_selecionado].copy()
                
                if municipio_selecionado != 'Todos':
                    df_plot = df_plot[df_plot['municipio'] == municipio_selecionado].copy()
            else:
                df_plot = df_semana.copy()
            
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
    
    # TAB 3: Rankings
    with tab3:
        st.subheader("🏆 Rankings de Municípios")
        
        if 'semana' in dados:
            df_semana = processar_dados_semana(dados['semana'])
            
            # Calcular médias por município
            df_ranking = df_semana.groupby(['municipio', 'estado']).agg({
                'PM2.5': 'mean',
                'PM10': 'mean',
                'O3': 'mean',
                'AQI': 'mean'
            }).reset_index()
            
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
                df_melhores_display = df_melhores[['Posição', 'municipio', 'estado', poluente_ranking]]
                df_melhores_display.columns = ['🏅', 'Município', 'UF', poluente_ranking]
                st.dataframe(df_melhores_display, hide_index=True, use_container_width=True)
            
            with col2:
                st.markdown(f"### ⚠️ Top 10 Pior Qualidade ({poluente_ranking})")
                df_piores = df_ranking.nlargest(10, poluente_ranking).copy()
                df_piores['Posição'] = range(1, len(df_piores) + 1)
                df_piores_display = df_piores[['Posição', 'municipio', 'estado', poluente_ranking]]
                df_piores_display.columns = ['⚠️', 'Município', 'UF', poluente_ranking]
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
    
    # TAB 4: Dados Brutos
    with tab4:
        st.subheader("📋 Dados Brutos")
        
        if 'semana' in dados:
            df_semana = processar_dados_semana(dados['semana'])
            
            st.info(f"📄 {len(df_semana):,} registros | 📊 {len(df_semana.columns)} colunas | 🏙️ {df_semana['municipio'].nunique():,} municípios")
            
            # Filtros
            col1, col2 = st.columns(2)
            
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
            
            # Aplicar filtros
            df_mostrar = df_semana.copy()
            
            if estados_filtro:
                df_mostrar = df_mostrar[df_mostrar['estado'].isin(estados_filtro)]
            
            if categorias_filtro:
                df_mostrar = df_mostrar[df_mostrar['Categoria'].isin(categorias_filtro)]
            
            # Mostrar dados
            st.dataframe(
                df_mostrar[['data', 'estado', 'municipio', 'PM2.5', 'PM10', 'O3', 'AQI', 'Categoria']],
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

