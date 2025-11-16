#!/bin/bash

clear
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Monitor de Qualidade do Ar - Brasil                      ║"
echo "║  Sistema Completo com Análise de Tendências ✅             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Funcionalidades:"
echo "   • Sistema de alertas com paginação"
echo "   • Análise de tendências temporais 🆕"
echo "   • Projeções futuras com IC 95% 🆕"
echo "   • Detecção de anomalias 🆕"
echo "   • Análise de sazonalidade 🆕"
echo ""
echo "🧹 Limpando cache..."
rm -rf .streamlit 2>/dev/null
rm -rf ~/.streamlit/cache 2>/dev/null

echo "🔄 Ativando ambiente virtual..."
source venv/bin/activate

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Dashboard: http://localhost:8501                          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "💡 Dicas:"
echo "   • Use o botão '🔄 Recarregar' se necessário"
echo "   • Tab 'Alertas': Filtre por Estados ou Municípios"
echo "   • Tab 'Análise de Tendências': Estatísticas avançadas 🆕"
echo "   • Pressione Ctrl+C para parar"
echo ""

streamlit run dashboard_qualidade_ar.py --server.port 8501

