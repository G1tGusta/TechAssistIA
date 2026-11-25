#!/usr/bin/env bash
# Inicia o TechAssist AI em modo servidor (Linux/macOS). PARA DEPOIS: veja servidor/LEIA-ME.md
cd "$(dirname "$0")/.." || exit 1
[ -x .venv/bin/python ] || { echo "Antes, execute ./IniciarTechAssist.sh uma vez."; exit 1; }
[ -f .env ] || { echo "Antes, execute ./IniciarTechAssist.sh uma vez para criar o .env."; exit 1; }
exec .venv/bin/python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501 \
    --server.headless true --browser.gatherUsageStats false
