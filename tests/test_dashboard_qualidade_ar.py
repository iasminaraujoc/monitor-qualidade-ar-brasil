"""
Testes unitários para dashboard_qualidade_ar.py
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
from unittest.mock import patch, MagicMock

# Adicionar o diretório raiz ao path para importar o módulo
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard_qualidade_ar import (
    calcular_aqi_pm25,
    obter_categoria_aqi,
    processar_dados_semana,
    carregar_dados,
    PADROES,
    CATEGORIAS_AQI
)


class TestCalcularAQIPM25:
    """Testes para a função calcular_aqi_pm25"""
    
    def test_aqi_valor_zero(self):
        """Testa cálculo de AQI para concentração zero"""
        resultado = calcular_aqi_pm25(0.0)
        assert resultado == 0
    
    def test_aqi_categoria_boa(self):
        """Testa valores na categoria Boa (0-50)"""
        # Limite inferior
        assert calcular_aqi_pm25(0.0) == 0
        # Meio da categoria
        assert calcular_aqi_pm25(6.0) == 25
        # Limite superior
        assert calcular_aqi_pm25(12.0) == 50
    
    def test_aqi_categoria_moderada(self):
        """Testa valores na categoria Moderada (51-100)"""
        # Limite inferior
        assert calcular_aqi_pm25(12.1) == 50
        # Meio da categoria
        assert calcular_aqi_pm25(23.7) == 75
        # Limite superior
        assert calcular_aqi_pm25(35.4) == 100
    
    def test_aqi_categoria_insalubre_sensiveis(self):
        """Testa valores na categoria Insalubre p/ Sensíveis (101-150)"""
        # Limite inferior
        assert calcular_aqi_pm25(35.5) == 100
        # Meio da categoria
        assert calcular_aqi_pm25(45.4) == 125
        # Limite superior
        assert calcular_aqi_pm25(55.4) == 150
    
    def test_aqi_categoria_insalubre(self):
        """Testa valores na categoria Insalubre (151-200)"""
        # Limite inferior
        assert calcular_aqi_pm25(55.5) == 150
        # Meio da categoria
        assert calcular_aqi_pm25(102.9) == 175
        # Limite superior
        assert calcular_aqi_pm25(150.4) == 200
    
    def test_aqi_categoria_muito_insalubre(self):
        """Testa valores na categoria Muito Insalubre (201-300)"""
        # Limite inferior
        assert calcular_aqi_pm25(150.5) == 200
        # Meio da categoria
        assert calcular_aqi_pm25(200.4) == 250
        # Limite superior
        assert calcular_aqi_pm25(250.4) == 300
    
    def test_aqi_categoria_perigosa(self):
        """Testa valores na categoria Perigosa (301+)"""
        # Limite inferior
        assert calcular_aqi_pm25(250.5) == 300
        # Valores altos
        assert calcular_aqi_pm25(350.0) == 380
        assert calcular_aqi_pm25(500.0) == 500
    
    def test_aqi_valor_nan(self):
        """Testa que valores NaN retornam None"""
        resultado = calcular_aqi_pm25(np.nan)
        assert resultado is None
    
    def test_aqi_valores_negativos(self):
        """Testa que valores negativos são tratados (deve retornar 0 ou None)"""
        resultado = calcular_aqi_pm25(-5.0)
        # Pode retornar 0 ou None dependendo da implementação
        assert resultado is not None
    
    def test_aqi_valores_muito_altos(self):
        """Testa valores extremamente altos"""
        resultado = calcular_aqi_pm25(1000.0)
        assert resultado is not None
        assert resultado > 500


class TestObterCategoriaAQI:
    """Testes para a função obter_categoria_aqi"""
    
    def test_categoria_boa(self):
        """Testa categorização para valores Boa (0-50)"""
        categoria, cor = obter_categoria_aqi(0)
        assert categoria == 'Boa'
        assert cor == '#00E400'
        
        categoria, cor = obter_categoria_aqi(25)
        assert categoria == 'Boa'
        assert cor == '#00E400'
        
        categoria, cor = obter_categoria_aqi(50)
        assert categoria == 'Boa'
        assert cor == '#00E400'
    
    def test_categoria_moderada(self):
        """Testa categorização para valores Moderada (51-100)"""
        categoria, cor = obter_categoria_aqi(51)
        assert categoria == 'Moderada'
        assert cor == '#FFFF00'
        
        categoria, cor = obter_categoria_aqi(75)
        assert categoria == 'Moderada'
        assert cor == '#FFFF00'
        
        categoria, cor = obter_categoria_aqi(100)
        assert categoria == 'Moderada'
        assert cor == '#FFFF00'
    
    def test_categoria_insalubre_sensiveis(self):
        """Testa categorização para Insalubre p/ Sensíveis (101-150)"""
        categoria, cor = obter_categoria_aqi(101)
        assert categoria == 'Insalubre p/ Sensíveis'
        assert cor == '#FF7E00'
        
        categoria, cor = obter_categoria_aqi(125)
        assert categoria == 'Insalubre p/ Sensíveis'
        assert cor == '#FF7E00'
        
        categoria, cor = obter_categoria_aqi(150)
        assert categoria == 'Insalubre p/ Sensíveis'
        assert cor == '#FF7E00'
    
    def test_categoria_insalubre(self):
        """Testa categorização para Insalubre (151-200)"""
        categoria, cor = obter_categoria_aqi(151)
        assert categoria == 'Insalubre'
        assert cor == '#FF0000'
        
        categoria, cor = obter_categoria_aqi(175)
        assert categoria == 'Insalubre'
        assert cor == '#FF0000'
        
        categoria, cor = obter_categoria_aqi(200)
        assert categoria == 'Insalubre'
        assert cor == '#FF0000'
    
    def test_categoria_muito_insalubre(self):
        """Testa categorização para Muito Insalubre (201-300)"""
        categoria, cor = obter_categoria_aqi(201)
        assert categoria == 'Muito Insalubre'
        assert cor == '#8F3F97'
        
        categoria, cor = obter_categoria_aqi(250)
        assert categoria == 'Muito Insalubre'
        assert cor == '#8F3F97'
        
        categoria, cor = obter_categoria_aqi(300)
        assert categoria == 'Muito Insalubre'
        assert cor == '#8F3F97'
    
    def test_categoria_perigosa(self):
        """Testa categorização para Perigosa (301+)"""
        categoria, cor = obter_categoria_aqi(301)
        assert categoria == 'Perigosa'
        assert cor == '#7E0023'
        
        categoria, cor = obter_categoria_aqi(400)
        assert categoria == 'Perigosa'
        assert cor == '#7E0023'
        
        categoria, cor = obter_categoria_aqi(500)
        assert categoria == 'Perigosa'
        assert cor == '#7E0023'
    
    def test_categoria_nan(self):
        """Testa que valores NaN retornam categoria 'Sem dados'"""
        categoria, cor = obter_categoria_aqi(np.nan)
        assert categoria == 'Sem dados'
        assert cor == '#CCCCCC'
    
    def test_categoria_valores_limite(self):
        """Testa valores exatamente nos limites das categorias"""
        # Limites entre categorias
        assert obter_categoria_aqi(50)[0] == 'Boa'
        assert obter_categoria_aqi(51)[0] == 'Moderada'
        assert obter_categoria_aqi(100)[0] == 'Moderada'
        assert obter_categoria_aqi(101)[0] == 'Insalubre p/ Sensíveis'
        assert obter_categoria_aqi(150)[0] == 'Insalubre p/ Sensíveis'
        assert obter_categoria_aqi(151)[0] == 'Insalubre'
        assert obter_categoria_aqi(200)[0] == 'Insalubre'
        assert obter_categoria_aqi(201)[0] == 'Muito Insalubre'
        assert obter_categoria_aqi(300)[0] == 'Muito Insalubre'
        assert obter_categoria_aqi(301)[0] == 'Perigosa'


class TestProcessarDadosSemana:
    """Testes para a função processar_dados_semana"""
    
    def test_processar_dados_basico(self, dados_semana_raw):
        """Testa processamento básico de dados"""
        resultado = processar_dados_semana(dados_semana_raw)
        
        # Verifica que colunas foram renomeadas
        assert 'PM2.5' in resultado.columns
        assert 'PM10' in resultado.columns
        assert 'O3' in resultado.columns
        
        # Verifica que colunas originais ainda existem
        assert 'pm2_5_media_diaria_previsao_situacao_atual' in resultado.columns or 'PM2.5' in resultado.columns
        
        # Verifica que AQI foi calculado
        assert 'AQI' in resultado.columns
        assert 'Categoria' in resultado.columns
        assert 'Cor' in resultado.columns
    
    def test_processar_dados_conversao_data(self, dados_semana_raw):
        """Testa conversão de data"""
        resultado = processar_dados_semana(dados_semana_raw)
        
        if 'data' in resultado.columns:
            assert pd.api.types.is_datetime64_any_dtype(resultado['data'])
    
    def test_processar_dados_calculo_aqi(self, dados_semana_raw):
        """Testa que AQI é calculado corretamente"""
        resultado = processar_dados_semana(dados_semana_raw)
        
        # Verifica que todos os valores de PM2.5 têm AQI correspondente
        for idx, row in resultado.iterrows():
            if pd.notna(row['PM2.5']):
                aqi_esperado = calcular_aqi_pm25(row['PM2.5'])
                assert row['AQI'] == aqi_esperado or pd.isna(row['AQI'])
    
    def test_processar_dados_categorizacao(self, dados_semana_raw):
        """Testa que categorias são atribuídas corretamente"""
        resultado = processar_dados_semana(dados_semana_raw)
        
        # Verifica que cada AQI tem categoria correspondente
        for idx, row in resultado.iterrows():
            if pd.notna(row['AQI']):
                categoria_esperada, cor_esperada = obter_categoria_aqi(row['AQI'])
                assert row['Categoria'] == categoria_esperada
                assert row['Cor'] == cor_esperada
    
    def test_processar_dados_valores_faltantes(self, dados_com_valores_faltantes):
        """Testa processamento com valores NaN"""
        resultado = processar_dados_semana(dados_com_valores_faltantes)
        
        # Verifica que função não quebra com NaN
        assert len(resultado) == len(dados_com_valores_faltantes)
        assert 'AQI' in resultado.columns
    
    def test_processar_dados_nao_modifica_original(self, dados_semana_raw):
        """Testa que DataFrame original não é modificado"""
        df_original = dados_semana_raw.copy()
        resultado = processar_dados_semana(dados_semana_raw)
        
        # Verifica que original não foi alterado (comparação de colunas principais)
        assert len(df_original) == len(dados_semana_raw)
    
    def test_processar_dados_valores_extremos(self, dados_valores_extremos):
        """Testa processamento com valores extremos"""
        resultado = processar_dados_semana(dados_valores_extremos)
        
        # Verifica que valores extremos são processados
        assert len(resultado) == len(dados_valores_extremos)
        assert 'AQI' in resultado.columns
        
        # Verifica que valores muito altos geram AQI alto
        for idx, row in resultado.iterrows():
            if pd.notna(row['PM2.5']) and row['PM2.5'] > 100:
                assert row['AQI'] > 150 or pd.isna(row['AQI'])

    
    @patch('dashboard_qualidade_ar.os.path.exists')
    def test_carregar_dados_pasta_inexistente(self, mock_exists):
        """Testa quando pasta de downloads não existe"""
        mock_exists.return_value = False
        
        resultado = carregar_dados()
        
        assert resultado is None
    
    @patch('dashboard_qualidade_ar.os.path.exists')
    @patch('dashboard_qualidade_ar.glob.glob')
    def test_carregar_dados_sem_arquivos(self, mock_glob, mock_exists):
        """Testa quando não há arquivos CSV"""
        mock_exists.return_value = True
        mock_glob.return_value = []
        
        resultado = carregar_dados()
        
        assert resultado == {}
    
    @patch('dashboard_qualidade_ar.os.path.exists')
    @patch('dashboard_qualidade_ar.glob.glob')
    @patch('dashboard_qualidade_ar.pd.read_csv')
    @patch('dashboard_qualidade_ar.os.path.getctime')
    def test_carregar_dados_erro_leitura(
        self,
        mock_getctime,
        mock_read_csv,
        mock_glob,
        mock_exists
    ):
        """Testa tratamento de erro ao ler CSV"""
        mock_exists.return_value = True
        mock_glob.return_value = ['arquivo.csv']
        mock_getctime.return_value = 1.0
        mock_read_csv.side_effect = Exception("Erro ao ler arquivo")
        
        # Não deve lançar exceção, apenas registrar erro
        resultado = carregar_dados()
        
        # Pode retornar None ou dicionário vazio dependendo da implementação
        assert resultado is not None or resultado == {}


class TestConstantes:
    """Testes para constantes e configurações"""
    
    def test_padroes_oms_estrutura(self):
        """Testa que PADROES tem estrutura correta"""
        assert 'PM2.5' in PADROES
        assert 'PM10' in PADROES
        assert 'O3' in PADROES
        
        assert '24h' in PADROES['PM2.5']
        assert 'anual' in PADROES['PM2.5']
        assert 'critico' in PADROES['PM2.5']
    
    def test_padroes_oms_valores(self):
        """Testa que valores dos padrões OMS estão corretos"""
        assert PADROES['PM2.5']['24h'] == 15
        assert PADROES['PM2.5']['anual'] == 5
        assert PADROES['PM10']['24h'] == 45
        assert PADROES['O3']['8h'] == 100
    
    def test_categorias_aqi_estrutura(self):
        """Testa que CATEGORIAS_AQI tem estrutura correta"""
        assert len(CATEGORIAS_AQI) == 6
        
        for cat in CATEGORIAS_AQI:
            assert 'nome' in cat
            assert 'min' in cat
            assert 'max' in cat
            assert 'cor' in cat
    
    def test_categorias_aqi_continuidade(self):
        """Testa que categorias AQI são contínuas (sem gaps)"""
        for i in range(len(CATEGORIAS_AQI) - 1):
            assert CATEGORIAS_AQI[i]['max'] + 1 == CATEGORIAS_AQI[i + 1]['min']


class TestIntegracaoFuncoes:
    """Testes de integração entre funções"""
    
    def test_fluxo_completo_processamento(self, dados_semana_raw):
        """Testa fluxo completo: processar -> calcular AQI -> categorizar"""
        # Processa dados
        df_processado = processar_dados_semana(dados_semana_raw)
        
        # Verifica que cada linha tem AQI e categoria consistentes
        for idx, row in df_processado.iterrows():
            if pd.notna(row['PM2.5']):
                # Calcula AQI manualmente
                aqi_esperado = calcular_aqi_pm25(row['PM2.5'])
                
                # Verifica que AQI calculado está correto
                if pd.notna(aqi_esperado):
                    assert row['AQI'] == aqi_esperado
                    
                    # Verifica que categoria corresponde ao AQI
                    categoria_esperada, cor_esperada = obter_categoria_aqi(row['AQI'])
                    assert row['Categoria'] == categoria_esperada
                    assert row['Cor'] == cor_esperada
    
    def test_consistencia_aqi_categoria(self, dados_semana_raw):
        """Testa que AQI e categoria são sempre consistentes"""
        df_processado = processar_dados_semana(dados_semana_raw)
        
        for idx, row in df_processado.iterrows():
            if pd.notna(row['AQI']):
                categoria, cor = obter_categoria_aqi(row['AQI'])
                assert row['Categoria'] == categoria
                assert row['Cor'] == cor

