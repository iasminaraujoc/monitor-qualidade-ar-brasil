"""
Módulo de Análise de Tendências
Sistema de Monitoramento de Qualidade do Ar - Brasil

Funcionalidades:
- Análise de tendências temporais (crescimento/decrescimento)
- Cálculo de médias móveis
- Detecção de sazonalidade
- Projeções futuras usando regressão linear
- Análise de variação e volatilidade
- Comparação de períodos
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy import stats
from typing import Dict, List, Tuple, Optional


class AnalisadorTendencias:
    """
    Classe para análise de tendências em dados de qualidade do ar
    """
    
    def __init__(self, df: pd.DataFrame, coluna_data: str = 'data'):
        """
        Inicializa o analisador de tendências
        
        Args:
            df: DataFrame com dados históricos
            coluna_data: Nome da coluna que contém as datas
        """
        self.df = df.copy()
        self.coluna_data = coluna_data
        
        # Garantir que a coluna de data está no formato datetime
        if self.coluna_data in self.df.columns:
            self.df[self.coluna_data] = pd.to_datetime(self.df[self.coluna_data], errors='coerce')
            self.df = self.df.sort_values(by=self.coluna_data)
    
    def calcular_tendencia_linear(self, poluente: str, 
                                   estado: Optional[str] = None,
                                   municipio: Optional[str] = None) -> Dict:
        """
        Calcula a tendência linear de um poluente ao longo do tempo
        
        Args:
            poluente: Nome do poluente (PM2.5, PM10, O3, etc.)
            estado: Filtrar por estado específico (opcional)
            municipio: Filtrar por município específico (opcional)
        
        Returns:
            Dicionário com informações da tendência:
            - slope: Coeficiente angular (taxa de mudança)
            - intercept: Intercepto
            - r_squared: R² (qualidade do ajuste)
            - p_value: Valor p (significância estatística)
            - tendencia: 'crescente', 'decrescente' ou 'estável'
            - taxa_mudanca_diaria: Taxa de mudança diária
            - taxa_mudanca_percentual: Taxa de mudança percentual
        """
        # Filtrar dados
        df_filtrado = self._filtrar_dados(estado, municipio)
        
        # Remover valores nulos
        df_clean = df_filtrado[[self.coluna_data, poluente]].dropna()
        
        if len(df_clean) < 3:
            return self._resultado_vazio()
        
        # Converter datas para números (dias desde o início)
        x = (df_clean[self.coluna_data] - df_clean[self.coluna_data].min()).dt.days.values
        y = df_clean[poluente].values
        
        # Regressão linear
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        # Determinar tendência
        if p_value < 0.05:  # Estatisticamente significativo
            if slope > 0.1:
                tendencia = 'crescente'
            elif slope < -0.1:
                tendencia = 'decrescente'
            else:
                tendencia = 'estável'
        else:
            tendencia = 'estável'
        
        # Calcular taxa de mudança percentual
        valor_medio = y.mean()
        taxa_mudanca_percentual = (slope / valor_medio * 100) if valor_medio != 0 else 0
        
        return {
            'slope': slope,
            'intercept': intercept,
            'r_squared': r_value ** 2,
            'p_value': p_value,
            'std_err': std_err,
            'tendencia': tendencia,
            'taxa_mudanca_diaria': slope,
            'taxa_mudanca_percentual': taxa_mudanca_percentual,
            'n_observacoes': len(df_clean),
            'valor_medio': valor_medio,
            'valor_inicial': y[0],
            'valor_final': y[-1],
            'data_inicial': df_clean[self.coluna_data].min(),
            'data_final': df_clean[self.coluna_data].max()
        }
    
    def calcular_media_movel(self, poluente: str, janela: int = 7,
                            estado: Optional[str] = None,
                            municipio: Optional[str] = None) -> pd.DataFrame:
        """
        Calcula a média móvel de um poluente
        
        Args:
            poluente: Nome do poluente
            janela: Tamanho da janela para média móvel (dias)
            estado: Filtrar por estado (opcional)
            municipio: Filtrar por município (opcional)
        
        Returns:
            DataFrame com valores originais e média móvel
        """
        df_filtrado = self._filtrar_dados(estado, municipio)
        
        # Agrupar por data e calcular média diária
        df_diario = df_filtrado.groupby(self.coluna_data)[poluente].mean().reset_index()
        
        # Calcular média móvel
        df_diario[f'{poluente}_MA{janela}'] = df_diario[poluente].rolling(
            window=janela, 
            center=False
        ).mean()
        
        return df_diario
    
    def projetar_valores_futuros(self, poluente: str, dias_futuros: int = 7,
                                estado: Optional[str] = None,
                                municipio: Optional[str] = None) -> pd.DataFrame:
        """
        Projeta valores futuros baseado na tendência linear
        
        Args:
            poluente: Nome do poluente
            dias_futuros: Número de dias para projetar
            estado: Filtrar por estado (opcional)
            municipio: Filtrar por município (opcional)
        
        Returns:
            DataFrame com datas futuras e valores projetados
        """
        tendencia = self.calcular_tendencia_linear(poluente, estado, municipio)
        
        if tendencia['n_observacoes'] < 3:
            return pd.DataFrame()
        
        # Última data dos dados
        data_final = tendencia['data_final']
        
        # Criar datas futuras
        datas_futuras = [data_final + timedelta(days=i+1) for i in range(dias_futuros)]
        
        # Calcular dias desde o início
        data_inicial = tendencia['data_inicial']
        dias_desde_inicio = [(d - data_inicial).days for d in datas_futuras]
        
        # Projetar valores
        valores_projetados = [
            tendencia['intercept'] + tendencia['slope'] * d 
            for d in dias_desde_inicio
        ]
        
        # Calcular intervalo de confiança (95%)
        std_err = tendencia['std_err']
        margem_erro = 1.96 * std_err * np.sqrt(dias_desde_inicio)
        
        return pd.DataFrame({
            'data': datas_futuras,
            'valor_projetado': valores_projetados,
            'limite_inferior': np.array(valores_projetados) - margem_erro,
            'limite_superior': np.array(valores_projetados) + margem_erro
        })
    
    def analisar_sazonalidade(self, poluente: str,
                             estado: Optional[str] = None,
                             municipio: Optional[str] = None) -> Dict:
        """
        Analisa padrões sazonais (por dia da semana e por mês)
        
        Args:
            poluente: Nome do poluente
            estado: Filtrar por estado (opcional)
            municipio: Filtrar por município (opcional)
        
        Returns:
            Dicionário com análise de sazonalidade
        """
        df_filtrado = self._filtrar_dados(estado, municipio)
        df_clean = df_filtrado[[self.coluna_data, poluente]].dropna()
        
        if len(df_clean) < 7:
            return {}
        
        # Adicionar colunas de tempo
        df_clean['dia_semana'] = df_clean[self.coluna_data].dt.dayofweek
        df_clean['dia_semana_nome'] = df_clean[self.coluna_data].dt.day_name()
        df_clean['mes'] = df_clean[self.coluna_data].dt.month
        df_clean['mes_nome'] = df_clean[self.coluna_data].dt.month_name()
        
        # Análise por dia da semana
        por_dia_semana = df_clean.groupby('dia_semana_nome')[poluente].agg([
            'mean', 'std', 'count'
        ]).round(2)
        
        # Análise por mês
        por_mes = df_clean.groupby('mes_nome')[poluente].agg([
            'mean', 'std', 'count'
        ]).round(2)
        
        # Identificar dia da semana com maior e menor valor
        dia_maior = por_dia_semana['mean'].idxmax()
        dia_menor = por_dia_semana['mean'].idxmin()
        
        # Identificar mês com maior e menor valor
        mes_maior = por_mes['mean'].idxmax() if len(por_mes) > 0 else None
        mes_menor = por_mes['mean'].idxmin() if len(por_mes) > 0 else None
        
        return {
            'por_dia_semana': por_dia_semana.to_dict('index'),
            'por_mes': por_mes.to_dict('index'),
            'dia_semana_maior': dia_maior,
            'dia_semana_menor': dia_menor,
            'mes_maior': mes_maior,
            'mes_menor': mes_menor,
            'variacao_semanal': por_dia_semana['mean'].std(),
            'variacao_mensal': por_mes['mean'].std() if len(por_mes) > 0 else 0
        }
    
    def calcular_volatilidade(self, poluente: str,
                             estado: Optional[str] = None,
                             municipio: Optional[str] = None) -> Dict:
        """
        Calcula métricas de volatilidade e variação
        
        Args:
            poluente: Nome do poluente
            estado: Filtrar por estado (opcional)
            municipio: Filtrar por município (opcional)
        
        Returns:
            Dicionário com métricas de volatilidade
        """
        df_filtrado = self._filtrar_dados(estado, municipio)
        valores = df_filtrado[poluente].dropna()
        
        if len(valores) < 2:
            return {}
        
        media = valores.mean()
        desvio_padrao = valores.std()
        coef_variacao = (desvio_padrao / media * 100) if media != 0 else 0
        
        return {
            'media': media,
            'mediana': valores.median(),
            'desvio_padrao': desvio_padrao,
            'coeficiente_variacao': coef_variacao,
            'minimo': valores.min(),
            'maximo': valores.max(),
            'amplitude': valores.max() - valores.min(),
            'percentil_25': valores.quantile(0.25),
            'percentil_75': valores.quantile(0.75),
            'amplitude_interquartil': valores.quantile(0.75) - valores.quantile(0.25)
        }
    
    def comparar_periodos(self, poluente: str, 
                         periodo1_inicio: str, periodo1_fim: str,
                         periodo2_inicio: str, periodo2_fim: str,
                         estado: Optional[str] = None,
                         municipio: Optional[str] = None) -> Dict:
        """
        Compara dois períodos de tempo
        
        Args:
            poluente: Nome do poluente
            periodo1_inicio: Data de início do período 1 (formato 'YYYY-MM-DD')
            periodo1_fim: Data de fim do período 1
            periodo2_inicio: Data de início do período 2
            periodo2_fim: Data de fim do período 2
            estado: Filtrar por estado (opcional)
            municipio: Filtrar por município (opcional)
        
        Returns:
            Dicionário com comparação entre períodos
        """
        df_filtrado = self._filtrar_dados(estado, municipio)
        
        # Converter strings para datetime
        p1_inicio = pd.to_datetime(periodo1_inicio)
        p1_fim = pd.to_datetime(periodo1_fim)
        p2_inicio = pd.to_datetime(periodo2_inicio)
        p2_fim = pd.to_datetime(periodo2_fim)
        
        # Filtrar por períodos
        periodo1 = df_filtrado[
            (df_filtrado[self.coluna_data] >= p1_inicio) & 
            (df_filtrado[self.coluna_data] <= p1_fim)
        ][poluente].dropna()
        
        periodo2 = df_filtrado[
            (df_filtrado[self.coluna_data] >= p2_inicio) & 
            (df_filtrado[self.coluna_data] <= p2_fim)
        ][poluente].dropna()
        
        if len(periodo1) == 0 or len(periodo2) == 0:
            return {}
        
        # Calcular estatísticas
        media1 = periodo1.mean()
        media2 = periodo2.mean()
        
        mudanca_absoluta = media2 - media1
        mudanca_percentual = (mudanca_absoluta / media1 * 100) if media1 != 0 else 0
        
        # Teste t para diferença estatística
        t_stat, p_value = stats.ttest_ind(periodo1, periodo2)
        diferenca_significativa = p_value < 0.05
        
        return {
            'periodo1': {
                'inicio': periodo1_inicio,
                'fim': periodo1_fim,
                'media': media1,
                'mediana': periodo1.median(),
                'desvio_padrao': periodo1.std(),
                'n_observacoes': len(periodo1)
            },
            'periodo2': {
                'inicio': periodo2_inicio,
                'fim': periodo2_fim,
                'media': media2,
                'mediana': periodo2.median(),
                'desvio_padrao': periodo2.std(),
                'n_observacoes': len(periodo2)
            },
            'comparacao': {
                'mudanca_absoluta': mudanca_absoluta,
                'mudanca_percentual': mudanca_percentual,
                't_statistic': t_stat,
                'p_value': p_value,
                'diferenca_significativa': diferenca_significativa,
                'interpretacao': self._interpretar_mudanca(mudanca_percentual, diferenca_significativa)
            }
        }
    
    def detectar_anomalias(self, poluente: str, 
                          limite_desvios: float = 2.5,
                          estado: Optional[str] = None,
                          municipio: Optional[str] = None) -> pd.DataFrame:
        """
        Detecta valores anômalos usando método de desvios padrão
        
        Args:
            poluente: Nome do poluente
            limite_desvios: Número de desvios padrão para considerar anomalia
            estado: Filtrar por estado (opcional)
            municipio: Filtrar por município (opcional)
        
        Returns:
            DataFrame com datas e valores anômalos
        """
        df_filtrado = self._filtrar_dados(estado, municipio)
        df_clean = df_filtrado[[self.coluna_data, poluente]].dropna()
        
        if len(df_clean) < 5:
            return pd.DataFrame()
        
        # Calcular média e desvio padrão
        media = df_clean[poluente].mean()
        desvio = df_clean[poluente].std()
        
        # Identificar anomalias
        df_clean['z_score'] = (df_clean[poluente] - media) / desvio
        df_clean['anomalia'] = abs(df_clean['z_score']) > limite_desvios
        
        # Filtrar apenas anomalias
        anomalias = df_clean[df_clean['anomalia']].copy()
        anomalias['tipo'] = anomalias['z_score'].apply(
            lambda x: 'Alta' if x > 0 else 'Baixa'
        )
        
        return anomalias[[self.coluna_data, poluente, 'z_score', 'tipo']]
    
    def gerar_relatorio_completo(self, poluente: str,
                                estado: Optional[str] = None,
                                municipio: Optional[str] = None) -> Dict:
        """
        Gera um relatório completo de análise de tendências
        
        Args:
            poluente: Nome do poluente
            estado: Filtrar por estado (opcional)
            municipio: Filtrar por município (opcional)
        
        Returns:
            Dicionário com análises completas
        """
        return {
            'tendencia_linear': self.calcular_tendencia_linear(poluente, estado, municipio),
            'volatilidade': self.calcular_volatilidade(poluente, estado, municipio),
            'sazonalidade': self.analisar_sazonalidade(poluente, estado, municipio),
            'anomalias': self.detectar_anomalias(poluente, estado=estado, municipio=municipio),
            'projecao_7_dias': self.projetar_valores_futuros(poluente, 7, estado, municipio)
        }
    
    # Métodos auxiliares privados
    
    def _filtrar_dados(self, estado: Optional[str] = None, 
                      municipio: Optional[str] = None) -> pd.DataFrame:
        """Filtra o DataFrame por estado e/ou município"""
        df_filtrado = self.df.copy()
        
        if estado and 'estado' in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado['estado'] == estado]
        
        if municipio and 'municipio' in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado['municipio'] == municipio]
        
        return df_filtrado
    
    def _resultado_vazio(self) -> Dict:
        """Retorna um resultado vazio para casos com dados insuficientes"""
        return {
            'slope': 0,
            'intercept': 0,
            'r_squared': 0,
            'p_value': 1,
            'std_err': 0,
            'tendencia': 'insuficiente',
            'taxa_mudanca_diaria': 0,
            'taxa_mudanca_percentual': 0,
            'n_observacoes': 0,
            'valor_medio': 0,
            'valor_inicial': 0,
            'valor_final': 0,
            'data_inicial': None,
            'data_final': None
        }
    
    def _interpretar_mudanca(self, mudanca_percentual: float, 
                            significativa: bool) -> str:
        """Interpreta a mudança percentual entre períodos"""
        if not significativa:
            return "Não há diferença estatisticamente significativa entre os períodos"
        
        if abs(mudanca_percentual) < 5:
            return f"Mudança pequena ({mudanca_percentual:.1f}%)"
        elif abs(mudanca_percentual) < 20:
            return f"Mudança moderada ({mudanca_percentual:.1f}%)"
        else:
            direcao = "aumento" if mudanca_percentual > 0 else "redução"
            return f"Mudança significativa: {direcao} de {abs(mudanca_percentual):.1f}%"


# Funções auxiliares para uso rápido

def calcular_tendencia(df: pd.DataFrame, poluente: str, **kwargs) -> Dict:
    """Função auxiliar para calcular tendência rapidamente"""
    analisador = AnalisadorTendencias(df)
    return analisador.calcular_tendencia_linear(poluente, **kwargs)


def projetar_futuro(df: pd.DataFrame, poluente: str, dias: int = 7, **kwargs) -> pd.DataFrame:
    """Função auxiliar para projetar valores futuros"""
    analisador = AnalisadorTendencias(df)
    return analisador.projetar_valores_futuros(poluente, dias, **kwargs)


def detectar_anomalias(df: pd.DataFrame, poluente: str, **kwargs) -> pd.DataFrame:
    """Função auxiliar para detectar anomalias"""
    analisador = AnalisadorTendencias(df)
    return analisador.detectar_anomalias(poluente, **kwargs)

