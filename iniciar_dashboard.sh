#!/bin/bash

# Script para iniciar o Dashboard de Qualidade do Ar

echo "🌫️ Monitor de Qualidade do Ar - Brasil"
echo "======================================="
echo ""

# Verificar se o ambiente virtual existe
if [ ! -d "venv" ]; then
    echo "❌ Ambiente virtual não encontrado!"
    echo "Execute primeiro:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Verificar se existem dados
if [ ! -d "downloads_inpe" ] || [ -z "$(ls -A downloads_inpe/*.csv 2>/dev/null)" ]; then
    echo "⚠️  Nenhum dado encontrado!"
    echo ""
    echo "Deseja coletar dados agora? (s/n)"
    read -r resposta
    
    if [ "$resposta" = "s" ] || [ "$resposta" = "S" ]; then
        echo ""
        echo "🔄 Iniciando coleta de dados..."
        source venv/bin/activate
        python3 coletar_inpe_sisam.py
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "✅ Dados coletados com sucesso!"
        else
            echo ""
            echo "❌ Erro ao coletar dados!"
            exit 1
        fi
    else
        echo ""
        echo "Execute primeiro: python3 coletar_inpe_sisam.py"
        exit 1
    fi
fi

echo ""
echo "🚀 Iniciando dashboard..."
echo ""

# Ativar ambiente virtual e executar Streamlit
source venv/bin/activate
streamlit run dashboard_qualidade_ar.py --server.port 8501 --server.headless true

# Caso o Streamlit seja interrompido
echo ""
echo "👋 Dashboard encerrado!"

