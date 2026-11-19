#!/usr/bin/env bash
# Inicia o TechAssist AI no Linux/macOS (cria o ambiente virtual e instala tudo na primeira vez).
cd "$(dirname "$0")" || exit 1

PY=$(command -v python3 || command -v python)
if [ -z "$PY" ] || ! "$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo "Python 3.10 ou superior nao encontrado."; exit 1
fi

# Ambiente virtual copiado de outro computador nao funciona: recria.
if [ -x .venv/bin/python ] && ! .venv/bin/python -c 'import sys' 2>/dev/null; then rm -rf .venv; fi
if [ ! -x .venv/bin/python ]; then
    echo "Criando ambiente virtual (somente na primeira vez)..."
    "$PY" -m venv .venv || { echo "Falha ao criar o ambiente virtual. No Debian/Ubuntu: sudo apt install python3-venv"; exit 1; }
fi

.venv/bin/python -c 'import streamlit, groq, dotenv' 2>/dev/null || \
    .venv/bin/python -m pip install -r requirements.txt || exit 1

if [ ! -f .env ]; then
    cp .env.example .env
    echo "Edite o arquivo .env (TECHNICIAN_PASSWORD e, para usar a IA, GROQ_API_KEY) e execute este script novamente."
    exit 0
fi

exec .venv/bin/python -m streamlit run app.py
