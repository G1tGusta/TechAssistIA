"""Diagnóstico do TechAssist AI: confere o ambiente e os arquivos e explica, em português, o que está errado.

Uso: dê dois cliques em Diagnostico.bat (ou execute: python diagnostico.py).
O relatório também é salvo em diagnostico.txt, para enviar a quem for ajudar.
"""
import ast
import importlib
import importlib.metadata
import json
import os
import socket
import sqlite3
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(errors="replace")   # evita erro de acentos no console do Windows
except Exception:
    pass

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))
ARQUIVOS = ["app.py", "database.py", "knowledge.py", "notificacoes.py", "versao.py",
            "base_conhecimento.json", "requirements.txt"]
MODULOS_LOCAIS = ["database", "knowledge", "notificacoes", "versao"]
CAMINHO_DB_USUARIO = None
linhas = []
contagem = {"ERRO": 0, "AVISO": 0}


def registrar(nivel, texto, dica=""):
    rotulo = {"OK": "[OK]   ", "AVISO": "[AVISO]", "ERRO": "[ERRO] ", "INFO": "[info] "}[nivel]
    linha = f"{rotulo} {texto}"
    if dica:
        linha += f"\n          -> {dica}"
    linhas.append(linha)
    print(linha)
    if nivel in contagem:
        contagem[nivel] += 1


def ler_env():
    valores = {}
    caminho = RAIZ / ".env"
    if caminho.exists():
        for bruta in caminho.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            bruta = bruta.strip()
            if bruta and not bruta.startswith("#") and "=" in bruta:
                chave, _, valor = bruta.partition("=")
                valores[chave.strip()] = valor.strip().strip('"').strip("'")
    return valores


def versao_tupla(texto):
    partes = []
    for p in texto.split(".")[:3]:
        digitos = "".join(c for c in p if c.isdigit())
        partes.append(int(digitos) if digitos else 0)
    return tuple(partes)


def main():
    print("=" * 60)
    print("TechAssist AI - diagnóstico")
    print("=" * 60)
    linhas.append("TechAssist AI - diagnóstico")
    env_inicial = ler_env()
    global CAMINHO_DB_USUARIO
    CAMINHO_DB_USUARIO = Path(os.getenv("TECHASSIST_DB", "").strip() or env_inicial.get("TECHASSIST_DB", "")
                              or RAIZ / "data" / "techassist.db")
    # Os testes abaixo usam um banco temporário, para não criar nem alterar o seu banco.
    os.environ["TECHASSIST_DB"] = str(Path(tempfile.mkdtemp()) / "diagnostico.db")
    registrar("INFO", f"Pasta do sistema: {RAIZ}")
    if RAIZ.parent.name.lower() == RAIZ.name.lower():
        registrar("AVISO", "Existe uma pasta com o mesmo nome dentro de outra (pasta dupla).",
                  "Confira se você está usando a pasta certa: copie o CONTEÚDO do zip para a pasta do sistema, sem criar uma pasta dentro da outra.")

    # 1) Python
    if sys.version_info >= (3, 10):
        registrar("OK", f"Python {sys.version.split()[0]}")
    else:
        registrar("ERRO", f"Python {sys.version.split()[0]} é antigo.", "Instale o Python 3.10 ou superior (python.org).")
    registrar("INFO", "Ambiente virtual (.venv) em uso" if ".venv" in sys.prefix else
              "Executando com o Python do sistema (normal para este diagnóstico).")

    # 2) arquivos
    faltando = [a for a in ARQUIVOS if not (RAIZ / a).exists()]
    if faltando:
        registrar("ERRO", "Arquivos faltando: " + ", ".join(faltando),
                  "Extraia o zip completo por cima da pasta do sistema (todos os arquivos, não só alguns).")
    else:
        registrar("OK", "Todos os arquivos principais estão presentes.")
    if not (RAIZ / ".env.example").exists():
        if (RAIZ / ".env").exists():
            registrar("INFO", "O arquivo .env.example não está na pasta (não impede nada: o .env já existe).")
        else:
            registrar("AVISO", "Não há .env nem .env.example.", "Execute IniciarTechAssist.bat: ele cria o .env sozinho.")

    # 3) sintaxe do app.py
    app_py = RAIZ / "app.py"
    arvore = None
    if app_py.exists():
        try:
            fonte = app_py.read_text(encoding="utf-8")
            arvore = ast.parse(fonte)
            registrar("OK", f"app.py sem erro de escrita ({len(fonte.splitlines())} linhas).")
        except SyntaxError as exc:
            registrar("ERRO", f"app.py está com erro na linha {exc.lineno}: {exc.msg}",
                      "O arquivo pode estar incompleto ou corrompido. Copie o app.py do zip novamente.")

    # 4) versão
    try:
        import versao
        registrar("OK", f"Versão do sistema: {versao.VERSAO}")
    except Exception as exc:
        registrar("ERRO", f"Não consegui ler a versão (versao.py): {exc}", "Copie o versao.py do zip.")

    # 5) o app.py importa nomes dos módulos: confere se cada um existe (pega arquivos de versões diferentes misturados)
    if arvore is not None:
        problemas = 0
        for no in ast.walk(arvore):
            if isinstance(no, ast.ImportFrom) and no.module in MODULOS_LOCAIS and (RAIZ / f"{no.module}.py").exists():
                try:
                    modulo = importlib.import_module(no.module)
                except Exception as exc:
                    registrar("ERRO", f"Não consegui abrir {no.module}.py: {exc}", f"Copie o {no.module}.py do zip.")
                    problemas += 1
                    continue
                ausentes = [n.name for n in no.names if not hasattr(modulo, n.name)]
                if ausentes:
                    problemas += 1
                    registrar("ERRO", f"{no.module}.py é de uma versão antiga: falta {', '.join(ausentes)}.",
                              f"Substitua o {no.module}.py pelo do zip mais recente. (Este é o erro 'cannot import name'.)")
        if not problemas:
            registrar("OK", "Os módulos do sistema são compatíveis entre si.")

    # 6) bibliotecas
    minimo = {"streamlit": (1, 36), "groq": (0, 9), "python-dotenv": (1, 0)}
    instalados = set()
    for pacote, versao_min in minimo.items():
        try:
            instalada = importlib.metadata.version(pacote)
            instalados.add("dotenv" if pacote == "python-dotenv" else pacote)
            if versao_tupla(instalada) >= versao_min:
                registrar("OK", f"{pacote} {instalada}")
            else:
                registrar("ERRO", f"{pacote} {instalada} é antigo (mínimo {'.'.join(map(str, versao_min))}).",
                          "Execute IniciarTechAssist.bat (ele atualiza) ou: python -m pip install -r requirements.txt")
        except importlib.metadata.PackageNotFoundError:
            registrar("ERRO", f"Biblioteca {pacote} não instalada neste Python.",
                      "Execute IniciarTechAssist.bat (instala sozinho; precisa de internet).")

    # 6b) importar de verdade (pega erros que só aparecem ao abrir, ex.: biblioteca incompatível com esta versão do Python)
    importou_streamlit = False
    for pacote in ("streamlit", "groq", "dotenv"):
        if pacote not in instalados:
            continue   # já foi apontado acima como não instalado
        try:
            importlib.import_module(pacote)
            if pacote == "streamlit":
                importou_streamlit = True
        except Exception as exc:
            registrar("ERRO", f"A biblioteca {pacote} está instalada, mas não abre: {type(exc).__name__}: {exc}",
                      "Execute: .venv/Scripts/python.exe -m pip install --upgrade -r requirements.txt  (se persistir, envie este relatório).")
    if instalados and not any(l.startswith("[ERRO]  A biblioteca") for l in linhas):
        registrar("OK", "As bibliotecas instaladas abrem normalmente neste Python.")

    # 6c) carregar a tela de entrada do sistema como o navegador faria (mostra o erro exato, se houver)
    if importou_streamlit and arvore is not None and not faltando:
        try:
            from streamlit.testing.v1 import AppTest
            teste = AppTest.from_file(str(app_py), default_timeout=60)
            teste.run()
            if teste.exception:
                for ex in teste.exception:
                    detalhe = getattr(ex, "message", None) or getattr(ex, "value", None) or str(ex)
                    registrar("ERRO", f"A tela de entrada do sistema falhou ao carregar: {detalhe}",
                              "Este é o erro que impede o sistema de abrir. Envie este relatório (diagnostico.txt).")
            else:
                titulos = [str(h.value) for h in teste.header] if hasattr(teste, "header") else []
                registrar("OK", "A tela de entrada do sistema carrega sem erros." +
                          (f" ({titulos[0]})" if titulos else ""))
        except Exception as exc:
            registrar("AVISO", f"Não foi possível simular a abertura da tela: {type(exc).__name__}: {exc}")

    # 6d) pergunta de e-mail do Streamlit (primeira execução)
    credenciais = Path.home() / ".streamlit" / "credentials.toml"
    if credenciais.exists():
        registrar("OK", "Streamlit já configurado neste usuário (não pede e-mail ao abrir).")
    else:
        registrar("INFO", "Streamlit ainda não foi configurado neste usuário.",
                  "Se a janela preta mostrar 'Email:', é só apertar Enter. O IniciarTechAssist.bat novo evita essa pergunta.")

    # 7) configuração
    env = ler_env()
    if not (RAIZ / ".env").exists():
        registrar("AVISO", "Arquivo .env não existe.", "Execute IniciarTechAssist.bat: ele cria o .env e abre para você preencher.")
    else:
        if env.get("TECHNICIAN_PASSWORD"):
            registrar("OK", ".env com a senha do técnico preenchida.")
        else:
            registrar("ERRO", "TECHNICIAN_PASSWORD está vazio no .env: ninguém entra como técnico.", "Abra o .env e defina a senha do técnico.")
        if env.get("GROQ_API_KEY"):
            registrar("OK", "GROQ_API_KEY preenchida (a IA fica ativa).")
        else:
            registrar("AVISO", "GROQ_API_KEY vazia: a IA fica desligada (a base de soluções e os chamados funcionam).")
        avisos = [c for c in ("NOTIFICAR_TEAMS_URL", "NOTIFICAR_WEBHOOK_URL", "NOTIFICAR_EMAIL_PARA") if env.get(c)]
        registrar("INFO", "Avisos para a TI configurados: " + (", ".join(avisos) if avisos else "nenhum (opcional)"))

    # 8) base de soluções
    base = RAIZ / "base_conhecimento.json"
    if base.exists():
        try:
            dados = json.loads(base.read_text(encoding="utf-8"))
            registrar("OK", f"base_conhecimento.json válido ({len(dados.get('entradas', []))} soluções).")
        except Exception as exc:
            registrar("ERRO", f"base_conhecimento.json com erro de digitação: {exc}",
                      "Corrija o arquivo (o sistema usa a última versão válida até lá).")

    # 9) banco de dados (somente leitura)
    caminho_db = CAMINHO_DB_USUARIO
    if caminho_db.exists():
        try:
            con = sqlite3.connect(f"file:{caminho_db}?mode=ro", uri=True, timeout=5)
            integridade = con.execute("PRAGMA integrity_check").fetchone()[0]
            try:
                chamados = con.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
            except sqlite3.Error:
                chamados = "?"
            con.close()
            if integridade == "ok":
                registrar("OK", f"Banco de dados íntegro ({chamados} chamados): {caminho_db}")
            else:
                registrar("ERRO", f"Banco de dados com problema: {integridade}", "Restaure um backup do banco.")
        except sqlite3.Error as exc:
            registrar("ERRO", f"Não consegui abrir o banco: {exc}", "Feche outras janelas do sistema ou restaure um backup.")
    else:
        registrar("INFO", f"Banco ainda não existe (será criado na primeira execução): {caminho_db}")

    # 10) porta
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            em_uso = s.connect_ex(("127.0.0.1", 8501)) == 0
    except OSError:
        em_uso = False
    if em_uso:
        registrar("AVISO", "A porta 8501 já está em uso.",
                  "Provavelmente o TechAssist já está aberto em outra janela. Abra http://localhost:8501 ou feche a janela antiga.")
    else:
        registrar("OK", "Porta 8501 livre.")

    print("=" * 60)
    resumo = f"RESULTADO: {contagem['ERRO']} erro(s), {contagem['AVISO']} aviso(s)."
    if not contagem["ERRO"]:
        resumo += " Nenhum problema impede o sistema de abrir."
    print(resumo)
    linhas.append(resumo)
    try:
        (RAIZ / "diagnostico.txt").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    except OSError:
        pass
    return 1 if contagem["ERRO"] else 0


if __name__ == "__main__":
    sys.exit(main())
