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
    if [ -f .env.example ]; then cp .env.example .env
    else printf 'GROQ_API_KEY=\nGROQ_MODEL=openai/gpt-oss-120b\nPESQUISA_WEB=on\nTECHNICIAN_PASSWORD=\n' > .env; fi
    echo "Edite o arquivo .env (TECHNICIAN_PASSWORD e, para usar a IA, GROQ_API_KEY) e execute este script novamente."
    exit 0
fi

# Evita a pergunta "Email:" do Streamlit na primeira execucao.
if [ ! -f "$HOME/.streamlit/credentials.toml" ]; then
    mkdir -p "$HOME/.streamlit" && printf '[general]\nemail = ""\n' > "$HOME/.streamlit/credentials.toml"
fi
exec .venv/bin/python -m streamlit run app.py --browser.gatherUsageStats false
