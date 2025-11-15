"""
Testes de integração para o sistema completo
"""
import pytest
import pandas as pd
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard_qualidade_ar import (
    carregar_dados,
    processar_dados_semana,
    calcular_aqi_pm25,
    obter_categoria_aqi
)


class TestIntegracaoCarregamentoProcessamento:
    """Testes de integração entre carregamento e processamento"""
    
    def test_integracao_carregar_processar(self, pasta_downloads_temporaria, dados_semana_raw):
        """Testa integração completa: carregar CSV -> processar"""
        # Cria arquivo CSV na pasta temporária
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        arquivo_semana = os.path.join(
            pasta_downloads_temporaria,
            f'dados_inpe_semana_epidemiologica_municipios_{timestamp}.csv'
        )
        dados_semana_raw.to_csv(arquivo_semana, index=False, encoding='utf-8')
        
        # Mock do carregar_dados para usar pasta temporária
        with patch('dashboard_qualidade_ar.os.path.exists', return_value=True), \
             patch('dashboard_qualidade_ar.glob.glob') as mock_glob, \
             patch('dashboard_qualidade_ar.os.path.getctime', return_value=1.0), \
             patch('dashboard_qualidade_ar.pd.read_csv', return_value=dados_semana_raw):
            
            mock_glob.side_effect = lambda pattern: [arquivo_semana] if 'semana' in pattern else []
            
            dados = carregar_dados()
            
            if dados and 'semana' in dados:
                df_processado = processar_dados_semana(dados['semana'])
                
                # Verifica que processamento foi bem-sucedido
                assert len(df_processado) == len(dados_semana_raw)
                assert 'AQI' in df_processado.columns
                assert 'Categoria' in df_processado.columns


class TestIntegracaoCalculos:
    """Testes de integração entre cálculos de AQI e categorização"""
    
    def test_integracao_aqi_categoria_valores_reais(self):
        """Testa integração com valores reais de concentração"""
        concentracoes = [5.0, 12.0, 25.0, 50.0, 100.0, 200.0]
        
        for conc in concentracoes:
            aqi = calcular_aqi_pm25(conc)
            if aqi is not None:
                categoria, cor = obter_categoria_aqi(aqi)
                
                # Verifica que categoria é válida
                assert categoria in [
                    'Boa', 'Moderada', 'Insalubre p/ Sensíveis',
                    'Insalubre', 'Muito Insalubre', 'Perigosa', 'Sem dados'
                ]
                assert cor.startswith('#')
                assert len(cor) == 7  # Formato hexadecimal
    
    def test_integracao_dataframe_completo(self, dados_semana_raw):
        """Testa processamento completo de DataFrame"""
        df_processado = processar_dados_semana(dados_semana_raw)
        
        # Verifica integridade dos dados
        assert len(df_processado) > 0
        
        # Verifica que todas as colunas necessárias existem
        colunas_esperadas = ['PM2.5', 'PM10', 'O3', 'AQI', 'Categoria', 'Cor']
        for col in colunas_esperadas:
            assert col in df_processado.columns
        
        # Verifica consistência: se tem PM2.5, deve ter AQI (ou NaN)
        for idx, row in df_processado.iterrows():
            if pd.notna(row['PM2.5']):
                # AQI pode ser calculado ou NaN
                assert 'AQI' in df_processado.columns
                
                if pd.notna(row['AQI']):
                    # Se tem AQI, deve ter categoria
                    assert pd.notna(row['Categoria'])
                    assert pd.notna(row['Cor'])


class TestIntegracaoAgregacoes:
    """Testes de integração com agregações de dados"""
    
    def test_agregacao_por_estado(self, dados_semana_raw):
        """Testa agregação por estado após processamento"""
        df_processado = processar_dados_semana(dados_semana_raw)
        
        # Agrega por estado (simula o que o dashboard faz)
        df_estados = df_processado.groupby('estado').agg({
            'PM2.5': 'mean',
            'PM10': 'mean',
            'AQI': 'mean',
            'municipio': 'count'
        }).reset_index()
        
        # Verifica que agregação foi bem-sucedida
        assert len(df_estados) > 0
        assert 'PM2.5' in df_estados.columns
        assert 'PM10' in df_estados.columns
        assert 'AQI' in df_estados.columns
    
    def test_agregacao_por_data(self, dados_semana_raw):
        """Testa agregação por data após processamento"""
        df_processado = processar_dados_semana(dados_semana_raw)
        
        # Verifica se coluna data existe
        if 'data' in df_processado.columns:
            # Agrupa por data (simula série temporal)
            df_temporal = df_processado.groupby('data').agg({
                'PM2.5': 'mean',
                'PM10': 'mean',
                'O3': 'mean'
            }).reset_index()
            
            # Verifica que agregação foi bem-sucedida
            assert len(df_temporal) > 0
            assert 'PM2.5' in df_temporal.columns
    
    def test_agregacao_por_municipio(self, dados_semana_raw):
        """Testa agregação por município (para rankings)"""
        df_processado = processar_dados_semana(dados_semana_raw)
        
        # Agrega por município e estado
        df_ranking = df_processado.groupby(['municipio', 'estado']).agg({
            'PM2.5': 'mean',
            'PM10': 'mean',
            'O3': 'mean',
            'AQI': 'mean'
        }).reset_index()
        
        # Verifica que agregação foi bem-sucedida
        assert len(df_ranking) > 0
        assert 'municipio' in df_ranking.columns
        assert 'estado' in df_ranking.columns


class TestIntegracaoValoresLimite:
    """Testes de integração com valores nos limites"""
    
    def test_valores_limite_oms(self, dados_semana_raw):
        """Testa comportamento com valores próximos aos limites OMS"""
        # Cria dados com valores próximos aos limites
        df_limites = pd.DataFrame({
            'date': ['2025-10-28'] * 4,
            'municipio': ['Cidade1', 'Cidade2', 'Cidade3', 'Cidade4'],
            'estado': ['SP'] * 4,
            'pm2_5_media_diaria_previsao_situacao_atual': [14.9, 15.0, 15.1, 35.0],
            'pm10_media_diaria_previsao_situacao_atual': [44.9, 45.0, 45.1, 150.0],
            'o3_media_diaria_previsao_situacao_atual': [99.9, 100.0, 100.1, 160.0]
        })
        
        df_processado = processar_dados_semana(df_limites)
        
        # Verifica que todos foram processados
        assert len(df_processado) == 4
        
        # Verifica que valores acima do limite têm AQI alto
        cidade_acima_pm25 = df_processado[df_processado['PM2.5'] > 15.0]
        if len(cidade_acima_pm25) > 0:
            assert cidade_acima_pm25.iloc[0]['AQI'] >= 50  # Pelo menos Moderada


class TestIntegracaoCasosExtremos:
    """Testes de integração com casos extremos"""
    
    def test_dataframe_vazio(self):
        """Testa processamento de DataFrame vazio"""
        df_vazio = pd.DataFrame(columns=[
            'date', 'municipio', 'estado',
            'pm2_5_media_diaria_previsao_situacao_atual',
            'pm10_media_diaria_previsao_situacao_atual',
            'o3_media_diaria_previsao_situacao_atual'
        ])
        
        df_processado = processar_dados_semana(df_vazio)
        
        # Deve retornar DataFrame vazio mas com colunas adicionais
        assert len(df_processado) == 0
        assert 'AQI' in df_processado.columns
    
    def test_dataframe_apenas_nan(self, dados_com_valores_faltantes):
        """Testa processamento quando todos os valores são NaN"""
        df_processado = processar_dados_semana(dados_com_valores_faltantes)
        
        # Deve processar sem erro
        assert len(df_processado) == len(dados_com_valores_faltantes)
    
    def test_dataframe_muitas_linhas(self):
        """Testa processamento de DataFrame grande"""
        # Cria DataFrame com 1000 linhas
        dados_grande = pd.DataFrame({
            'date': ['2025-10-28'] * 1000,
            'municipio': [f'Cidade{i}' for i in range(1000)],
            'estado': ['SP'] * 1000,
            'pm2_5_media_diaria_previsao_situacao_atual': [10.0 + (i % 50) for i in range(1000)],
            'pm10_media_diaria_previsao_situacao_atual': [20.0 + (i % 50) for i in range(1000)],
            'o3_media_diaria_previsao_situacao_atual': [80.0 + (i % 30) for i in range(1000)]
        })
        
        df_processado = processar_dados_semana(dados_grande)
        
        # Verifica que processou todas as linhas
        assert len(df_processado) == 1000
        assert 'AQI' in df_processado.columns
        
        # Verifica que todos os AQIs foram calculados (ou são NaN)
        assert df_processado['AQI'].notna().sum() > 0

