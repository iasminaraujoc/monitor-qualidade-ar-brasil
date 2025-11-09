"""
Fixtures compartilhadas para os testes
"""
import pytest
import pandas as pd
import os
import tempfile
import shutil
from datetime import datetime, timedelta


@pytest.fixture
def dados_semana_raw():
    """
    DataFrame simulado com estrutura similar aos dados do INPE
    """
    data = {
        'date': [
            '2025-10-28', '2025-10-28', '2025-10-29', '2025-10-29',
            '2025-10-30', '2025-10-30'
        ],
        'municipio': [
            'São Paulo', 'Rio de Janeiro', 'São Paulo', 'Rio de Janeiro',
            'São Paulo', 'Belo Horizonte'
        ],
        'estado': ['SP', 'RJ', 'SP', 'RJ', 'SP', 'MG'],
        'pm2_5_media_diaria_previsao_situacao_atual': [12.5, 15.8, 18.2, 20.1, 10.5, 8.3],
        'pm10_media_diaria_previsao_situacao_atual': [25.3, 30.1, 35.5, 40.2, 22.1, 18.5],
        'o3_media_diaria_previsao_situacao_atual': [85.2, 92.5, 95.8, 98.3, 80.1, 75.4]
    }
    return pd.DataFrame(data)


@pytest.fixture
def dados_semana_processados():
    """
    DataFrame já processado com colunas normalizadas
    """
    data = {
        'date': ['2025-10-28', '2025-10-29', '2025-10-30'],
        'data': pd.to_datetime(['2025-10-28', '2025-10-29', '2025-10-30']),
        'municipio': ['São Paulo', 'Rio de Janeiro', 'Belo Horizonte'],
        'estado': ['SP', 'RJ', 'MG'],
        'PM2.5': [12.5, 15.8, 10.5],
        'PM10': [25.3, 30.1, 22.1],
        'O3': [85.2, 92.5, 80.1],
        'AQI': [52, 66, 44],
        'Categoria': ['Moderada', 'Moderada', 'Boa'],
        'Cor': ['#FFFF00', '#FFFF00', '#00E400']
    }
    return pd.DataFrame(data)


@pytest.fixture
def dados_com_valores_faltantes():
    """
    DataFrame com valores NaN para testar tratamento de dados faltantes
    """
    data = {
        'date': ['2025-10-28', '2025-10-29', '2025-10-30'],
        'municipio': ['São Paulo', 'Rio de Janeiro', 'Belo Horizonte'],
        'estado': ['SP', 'RJ', 'MG'],
        'pm2_5_media_diaria_previsao_situacao_atual': [12.5, None, 10.5],
        'pm10_media_diaria_previsao_situacao_atual': [25.3, 30.1, None],
        'o3_media_diaria_previsao_situacao_atual': [None, 92.5, 80.1]
    }
    return pd.DataFrame(data)


@pytest.fixture
def dados_valores_extremos():
    """
    DataFrame com valores extremos para testar limites do AQI
    """
    data = {
        'date': ['2025-10-28', '2025-10-28', '2025-10-28', '2025-10-28'],
        'municipio': ['Cidade1', 'Cidade2', 'Cidade3', 'Cidade4'],
        'estado': ['SP', 'SP', 'SP', 'SP'],
        'pm2_5_media_diaria_previsao_situacao_atual': [5.0, 150.0, 300.0, 0.0],
        'pm10_media_diaria_previsao_situacao_atual': [10.0, 200.0, 400.0, 0.0],
        'o3_media_diaria_previsao_situacao_atual': [50.0, 150.0, 250.0, 0.0]
    }
    return pd.DataFrame(data)


@pytest.fixture
def pasta_downloads_temporaria():
    """
    Cria uma pasta temporária para simular downloads_inpe/
    Retorna o caminho e limpa após os testes
    """
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def arquivo_csv_semana(pasta_downloads_temporaria, dados_semana_raw):
    """
    Cria um arquivo CSV simulado na pasta temporária
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f'dados_inpe_semana_epidemiologica_municipios_{timestamp}.csv'
    caminho = os.path.join(pasta_downloads_temporaria, nome_arquivo)
    dados_semana_raw.to_csv(caminho, index=False, encoding='utf-8')
    return caminho


@pytest.fixture
def arquivo_csv_hoje(pasta_downloads_temporaria):
    """
    Cria um arquivo CSV simulado de dados de hoje
    """
    dados_hoje = pd.DataFrame({
        'estado': ['SP', 'RJ', 'MG'],
        'estado_nome': ['São Paulo', 'Rio de Janeiro', 'Minas Gerais'],
        'data_coleta': [datetime.now().isoformat()] * 3,
        'PM2.5': [12.5, 15.8, 10.5],
        'PM10': [25.3, 30.1, 22.1]
    })
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f'dados_inpe_hoje_{timestamp}.csv'
    caminho = os.path.join(pasta_downloads_temporaria, nome_arquivo)
    dados_hoje.to_csv(caminho, index=False, encoding='utf-8')
    return caminho


@pytest.fixture
def concentracoes_pm25_teste():
    """
    Dicionário com concentrações de PM2.5 e AQI esperado
    """
    return {
        0.0: 0,      # Mínimo
        5.0: 21,     # Boa
        12.0: 50,    # Limite Boa
        12.1: 50,    # Início Moderada
        23.7: 75,    # Moderada
        35.4: 100,   # Limite Moderada
        35.5: 100,   # Início Insalubre p/ Sensíveis
        45.4: 125,   # Insalubre p/ Sensíveis
        55.4: 150,   # Limite Insalubre p/ Sensíveis
        55.5: 150,   # Início Insalubre
        122.9: 200,  # Insalubre
        150.4: 200,  # Limite Insalubre
        150.5: 200,  # Início Muito Insalubre
        200.4: 300,  # Muito Insalubre
        250.4: 300,  # Limite Muito Insalubre
        250.5: 300,  # Início Perigosa
        350.0: 380,  # Perigosa
        500.0: 500   # Extremo
    }


@pytest.fixture
def categorias_aqi_esperadas():
    """
    Mapeamento de AQI para categorias esperadas
    """
    return {
        0: ('Boa', '#00E400'),
        25: ('Boa', '#00E400'),
        50: ('Boa', '#00E400'),
        51: ('Moderada', '#FFFF00'),
        75: ('Moderada', '#FFFF00'),
        100: ('Moderada', '#FFFF00'),
        101: ('Insalubre p/ Sensíveis', '#FF7E00'),
        125: ('Insalubre p/ Sensíveis', '#FF7E00'),
        150: ('Insalubre p/ Sensíveis', '#FF7E00'),
        151: ('Insalubre', '#FF0000'),
        175: ('Insalubre', '#FF0000'),
        200: ('Insalubre', '#FF0000'),
        201: ('Muito Insalubre', '#8F3F97'),
        250: ('Muito Insalubre', '#8F3F97'),
        300: ('Muito Insalubre', '#8F3F97'),
        301: ('Perigosa', '#7E0023'),
        400: ('Perigosa', '#7E0023'),
        500: ('Perigosa', '#7E0023')
    }

