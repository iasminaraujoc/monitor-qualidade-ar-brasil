"""
Sistema de Alertas de Qualidade do Ar
Detecta situações críticas, alertas e melhorias baseado nos dados coletados
"""

import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

# Padrões de referência (OMS 2021)
LIMITES_OMS = {
    'PM2.5': 15,
    'PM10': 45,
    'O3': 100
}

LIMITES_CRITICOS = {
    'PM2.5': 35,
    'PM10': 150,
    'O3': 160
}

# Níveis de alerta
NIVEIS_ALERTA = {
    'critico': {
        'cor': '#FF0000',
        'icone': '🚨',
        'prioridade': 4,
        'nome': 'CRÍTICO'
    },
    'alerta': {
        'cor': '#FF7E00',
        'icone': '⚠️',
        'prioridade': 3,
        'nome': 'ALERTA'
    },
    'aviso': {
        'cor': '#FFFF00',
        'icone': '⚡',
        'prioridade': 2,
        'nome': 'AVISO'
    },
    'melhoria': {
        'cor': '#00E400',
        'icone': '✅',
        'prioridade': 1,
        'nome': 'MELHORIA'
    }
}

# Recomendações de saúde por categoria AQI
RECOMENDACOES_SAUDE = {
    'Boa': {
        'populacao_geral': 'Qualidade do ar excelente. Ideal para atividades ao ar livre.',
        'grupos_sensiveis': 'Nenhuma restrição.'
    },
    'Moderada': {
        'populacao_geral': 'Qualidade do ar aceitável para a maioria das pessoas.',
        'grupos_sensiveis': 'Pessoas extremamente sensíveis devem considerar reduzir esforços prolongados ao ar livre.'
    },
    'Insalubre p/ Sensíveis': {
        'populacao_geral': 'A população em geral não é afetada.',
        'grupos_sensiveis': 'Crianças, idosos e pessoas com doenças respiratórias ou cardíacas devem reduzir esforços prolongados ao ar livre.'
    },
    'Insalubre': {
        'populacao_geral': 'Todos podem começar a sentir efeitos na saúde. Evite atividades físicas intensas ao ar livre.',
        'grupos_sensiveis': 'Grupos sensíveis devem evitar esforços ao ar livre. Use máscaras se necessário sair.'
    },
    'Muito Insalubre': {
        'populacao_geral': 'ALERTA DE SAÚDE: Todos podem experimentar efeitos graves. Permaneça em ambientes fechados.',
        'grupos_sensiveis': 'Grupos sensíveis devem permanecer em ambientes fechados e evitar qualquer atividade ao ar livre.'
    },
    'Perigosa': {
        'populacao_geral': 'EMERGÊNCIA DE SAÚDE: Toda a população está em risco. Permaneça em ambientes fechados com portas e janelas fechadas.',
        'grupos_sensiveis': 'Grupos sensíveis devem procurar atendimento médico se apresentarem sintomas.'
    }
}

def calcular_variacao_percentual(valor_atual, valor_referencia):
    """Calcula variação percentual entre dois valores"""
    if pd.isna(valor_atual) or pd.isna(valor_referencia) or valor_referencia == 0:
        return None
    return ((valor_atual - valor_referencia) / valor_referencia) * 100

def criar_alerta(
    nivel: str,
    tipo: str,
    regiao: str,
    regiao_tipo: str,
    poluente: str,
    valor_atual: float,
    valor_referencia: float = None,
    variacao_pct: float = None,
    categoria_aqi: str = None
) -> Dict[str, Any]:
    """Cria um objeto de alerta estruturado"""
    
    nivel_info = NIVEIS_ALERTA.get(nivel, NIVEIS_ALERTA['aviso'])
    
    # Construir mensagem
    if tipo == 'limite_critico':
        mensagem = f"{poluente} em nível CRÍTICO ({valor_atual:.1f} µg/m³) - Limite crítico: {valor_referencia:.1f}"
    elif tipo == 'limite_oms':
        mensagem = f"{poluente} acima do limite OMS ({valor_atual:.1f} µg/m³) - Limite: {valor_referencia:.1f}"
    elif tipo == 'mudanca_brusca_aumento':
        mensagem = f"{poluente} com aumento brusco de {variacao_pct:+.1f}% vs média histórica"
    elif tipo == 'mudanca_brusca_queda':
        mensagem = f"{poluente} com queda brusca de {variacao_pct:.1f}% vs média histórica"
    elif tipo == 'melhoria':
        mensagem = f"{poluente} voltou ao padrão OMS ({valor_atual:.1f} µg/m³)"
    elif tipo == 'tendencia_piora':
        mensagem = f"{poluente} em tendência de piora nas últimas semanas"
    else:
        mensagem = f"{poluente}: {valor_atual:.1f} µg/m³"
    
    # Recomendação de saúde
    recomendacao = ''
    if categoria_aqi and categoria_aqi in RECOMENDACOES_SAUDE:
        rec = RECOMENDACOES_SAUDE[categoria_aqi]
        recomendacao = f"**População geral:** {rec['populacao_geral']}\n\n**Grupos sensíveis:** {rec['grupos_sensiveis']}"
    
    return {
        'id': f"alerta_{datetime.now().strftime('%Y%m%d%H%M%S')}_{regiao}_{poluente}".replace(' ', '_'),
        'timestamp': datetime.now(),
        'nivel': nivel,
        'tipo': tipo,
        'regiao': regiao,
        'regiao_tipo': regiao_tipo,
        'poluente': poluente,
        'valor_atual': valor_atual,
        'valor_referencia': valor_referencia,
        'variacao_pct': variacao_pct,
        'categoria_aqi': categoria_aqi,
        'mensagem': mensagem,
        'recomendacao': recomendacao,
        'cor': nivel_info['cor'],
        'icone': nivel_info['icone'],
        'prioridade': nivel_info['prioridade'],
        'nome_nivel': nivel_info['nome']
    }

def analisar_alertas_estado(df_hoje: pd.DataFrame, df_semana: pd.DataFrame = None) -> List[Dict[str, Any]]:
    """
    Analisa dados de estados (hoje) e gera alertas
    
    Args:
        df_hoje: DataFrame com dados diários por estado
        df_semana: DataFrame com dados históricos (opcional, para calcular variações)
    
    Returns:
        Lista de alertas detectados
    """
    alertas = []
    
    if df_hoje is None or len(df_hoje) == 0:
        return alertas
    
    # Calcular médias históricas se disponível
    medias_historicas = {}
    if df_semana is not None and len(df_semana) > 0:
        if 'estado' in df_semana.columns:
            for poluente in ['PM2.5', 'PM10', 'O3']:
                if poluente in df_semana.columns:
                    medias_historicas[poluente] = df_semana.groupby('estado')[poluente].mean().to_dict()
    
    # Analisar cada estado
    for _, row in df_hoje.iterrows():
        estado = row.get('estado_nome', row.get('estado', 'Desconhecido'))
        estado_sigla = row.get('estado', '')
        categoria_aqi = row.get('Categoria', None)
        
        # Analisar cada poluente
        for poluente in ['PM2.5', 'PM10', 'O3']:
            if poluente not in row or pd.isna(row[poluente]):
                continue
            
            valor_atual = row[poluente]
            limite_oms = LIMITES_OMS.get(poluente)
            limite_critico = LIMITES_CRITICOS.get(poluente)
            
            # 1. Verificar limite crítico
            if limite_critico and valor_atual >= limite_critico:
                alertas.append(criar_alerta(
                    nivel='critico',
                    tipo='limite_critico',
                    regiao=estado,
                    regiao_tipo='estado',
                    poluente=poluente,
                    valor_atual=valor_atual,
                    valor_referencia=limite_critico,
                    categoria_aqi=categoria_aqi
                ))
            
            # 2. Verificar limite OMS (se não for crítico)
            elif limite_oms and valor_atual > limite_oms:
                alertas.append(criar_alerta(
                    nivel='alerta',
                    tipo='limite_oms',
                    regiao=estado,
                    regiao_tipo='estado',
                    poluente=poluente,
                    valor_atual=valor_atual,
                    valor_referencia=limite_oms,
                    categoria_aqi=categoria_aqi
                ))
            
            # 3. Verificar melhoria (estava acima e voltou ao normal)
            elif limite_oms and valor_atual <= limite_oms:
                # Verificar se a média histórica estava acima
                if poluente in medias_historicas and estado_sigla in medias_historicas[poluente]:
                    media_historica = medias_historicas[poluente][estado_sigla]
                    if media_historica > limite_oms:
                        alertas.append(criar_alerta(
                            nivel='melhoria',
                            tipo='melhoria',
                            regiao=estado,
                            regiao_tipo='estado',
                            poluente=poluente,
                            valor_atual=valor_atual,
                            valor_referencia=limite_oms,
                            categoria_aqi=categoria_aqi
                        ))
            
            # 4. Verificar mudanças bruscas vs histórico
            if poluente in medias_historicas and estado_sigla in medias_historicas[poluente]:
                media_historica = medias_historicas[poluente][estado_sigla]
                variacao_pct = calcular_variacao_percentual(valor_atual, media_historica)
                
                if variacao_pct is not None:
                    # Aumento brusco (>30%)
                    if variacao_pct > 30:
                        alertas.append(criar_alerta(
                            nivel='aviso',
                            tipo='mudanca_brusca_aumento',
                            regiao=estado,
                            regiao_tipo='estado',
                            poluente=poluente,
                            valor_atual=valor_atual,
                            valor_referencia=media_historica,
                            variacao_pct=variacao_pct,
                            categoria_aqi=categoria_aqi
                        ))
                    # Queda brusca (<-30%)
                    elif variacao_pct < -30:
                        alertas.append(criar_alerta(
                            nivel='melhoria',
                            tipo='mudanca_brusca_queda',
                            regiao=estado,
                            regiao_tipo='estado',
                            poluente=poluente,
                            valor_atual=valor_atual,
                            valor_referencia=media_historica,
                            variacao_pct=variacao_pct,
                            categoria_aqi=categoria_aqi
                        ))
    
    # Ordenar por prioridade (maior prioridade primeiro)
    alertas.sort(key=lambda x: x['prioridade'], reverse=True)
    
    return alertas

def analisar_alertas_municipio(df_semana: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Analisa dados de municípios (série temporal) e gera alertas
    OTIMIZADO: Agrupa dados antes de processar para melhor performance
    
    Args:
        df_semana: DataFrame com dados semanais por município
    
    Returns:
        Lista de alertas detectados
    """
    alertas = []
    
    if df_semana is None or len(df_semana) == 0:
        return alertas
    
    # Calcular médias por município
    if 'municipio' not in df_semana.columns or 'estado' not in df_semana.columns:
        return alertas
    
    colunas_agg = {}
    for col in ['PM2.5', 'PM10', 'O3', 'AQI']:
        if col in df_semana.columns:
            colunas_agg[col] = 'mean'
    
    if not colunas_agg:
        return alertas
    
    # Otimização: Fazer apenas um groupby com todas as colunas necessárias
    if 'Categoria' in df_semana.columns:
        colunas_agg['Categoria'] = lambda x: x.mode()[0] if len(x.mode()) > 0 else 'Sem dados'
    
    df_municipios = df_semana.groupby(['municipio', 'estado'], as_index=False).agg(colunas_agg)
    
    # Analisar municípios consistentemente acima dos limites
    for _, row in df_municipios.iterrows():
        municipio = row['municipio']
        estado = row['estado']
        regiao = f"{municipio}/{estado}"
        categoria_aqi = row.get('Categoria', None)
        
        for poluente in ['PM2.5', 'PM10', 'O3']:
            if poluente not in row or pd.isna(row[poluente]):
                continue
            
            valor_medio = row[poluente]
            limite_oms = LIMITES_OMS.get(poluente)
            limite_critico = LIMITES_CRITICOS.get(poluente)
            
            # Crítico: média consistentemente acima do limite crítico
            if limite_critico and valor_medio >= limite_critico:
                alertas.append(criar_alerta(
                    nivel='critico',
                    tipo='limite_critico',
                    regiao=regiao,
                    regiao_tipo='municipio',
                    poluente=poluente,
                    valor_atual=valor_medio,
                    valor_referencia=limite_critico,
                    categoria_aqi=categoria_aqi
                ))
            
            # Alerta: média consistentemente acima do limite OMS
            elif limite_oms and valor_medio > limite_oms:
                alertas.append(criar_alerta(
                    nivel='alerta',
                    tipo='limite_oms',
                    regiao=regiao,
                    regiao_tipo='municipio',
                    poluente=poluente,
                    valor_atual=valor_medio,
                    valor_referencia=limite_oms,
                    categoria_aqi=categoria_aqi
                ))
    
    # NOTA: Análise de tendências temporais foi removida para melhorar performance
    # Com 195k registros, a análise de tendências causava lentidão no dashboard
    
    # Ordenar por prioridade
    alertas.sort(key=lambda x: x['prioridade'], reverse=True)
    
    return alertas

def gerar_todos_alertas(dados: Dict) -> Dict[str, List[Dict[str, Any]]]:
    """
    Gera todos os alertas a partir dos dados carregados
    
    Args:
        dados: Dicionário com 'hoje' e 'semana' DataFrames
    
    Returns:
        Dicionário com alertas separados por tipo
    """
    resultado = {
        'estados': [],
        'municipios': [],
        'todos': [],
        'por_nivel': {
            'critico': [],
            'alerta': [],
            'aviso': [],
            'melhoria': []
        },
        'estatisticas': {
            'total': 0,
            'criticos': 0,
            'alertas': 0,
            'avisos': 0,
            'melhorias': 0
        }
    }
    
    df_hoje = dados.get('hoje')
    df_semana = dados.get('semana')
    
    # Alertas de estados
    if df_hoje is not None:
        alertas_estados = analisar_alertas_estado(df_hoje, df_semana)
        resultado['estados'] = alertas_estados
        resultado['todos'].extend(alertas_estados)
    
    # Alertas de municípios (TODOS os alertas, sem limitação)
    if df_semana is not None:
        alertas_municipios = analisar_alertas_municipio(df_semana)
        # Ordenar por prioridade (críticos > alertas > avisos) e depois por maior concentração
        alertas_municipios_sorted = sorted(
            alertas_municipios, 
            key=lambda x: (x['prioridade'], x['valor_atual']), 
            reverse=True
        )
        # Manter TODOS os alertas (paginação será feita no dashboard)
        resultado['municipios'] = alertas_municipios_sorted
        resultado['todos'].extend(alertas_municipios_sorted)
    
    # Ordenar todos por prioridade
    resultado['todos'].sort(key=lambda x: x['prioridade'], reverse=True)
    
    # Organizar por nível
    for alerta in resultado['todos']:
        nivel = alerta['nivel']
        if nivel in resultado['por_nivel']:
            resultado['por_nivel'][nivel].append(alerta)
    
    # Calcular estatísticas
    resultado['estatisticas']['total'] = len(resultado['todos'])
    resultado['estatisticas']['criticos'] = len(resultado['por_nivel']['critico'])
    resultado['estatisticas']['alertas'] = len(resultado['por_nivel']['alerta'])
    resultado['estatisticas']['avisos'] = len(resultado['por_nivel']['aviso'])
    resultado['estatisticas']['melhorias'] = len(resultado['por_nivel']['melhoria'])
    
    return resultado

def obter_recomendacao_categoria(categoria: str) -> Dict[str, str]:
    """Retorna recomendações de saúde para uma categoria AQI"""
    return RECOMENDACOES_SAUDE.get(categoria, {
        'populacao_geral': 'Sem dados disponíveis.',
        'grupos_sensiveis': 'Sem dados disponíveis.'
    })

