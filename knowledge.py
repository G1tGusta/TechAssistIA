"""Base de soluções conhecidas da TI.

Consultada ANTES de chamar a API de IA: se a mensagem do funcionário combina
com um problema já conhecido, o passo a passo é enviado direto, sem custo de API.
Para adicionar ou ajustar soluções, edite o arquivo base_conhecimento.json.
"""
import json
import re
import unicodedata
from pathlib import Path

KB_PATH = Path(__file__).parent / "base_conhecimento.json"
_cache = {"mtime": None, "entries": []}


def _norm(text):
    """Minúsculas, sem acentos e sem pontuação, para comparar textos."""
    text = unicodedata.normalize("NFKD", str(text).lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def load_entries():
    """Lê o JSON (recarrega sozinho quando o arquivo é alterado)."""
    try:
        mtime = KB_PATH.stat().st_mtime
    except OSError:
        return []
    if _cache["mtime"] != mtime:
        try:
            data = json.loads(KB_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            # JSON com erro de digitação: mantém a última versão válida.
            return _cache["entries"]
        required = ("id", "titulo", "palavras_chave", "passos")
        entries = [e for e in data.get("entradas", []) if all(e.get(k) for k in required)]
        _cache["mtime"] = mtime
        _cache["entries"] = entries
    return _cache["entries"]


def get_entry(entry_id):
    return next((e for e in load_entries() if e["id"] == entry_id), None)


def find_solution(text, ignore_ids=()):
    """Retorna a solução que melhor combina com o texto, ou None."""
    norm = _norm(text)
    if not norm:
        return None
    best, best_score = None, 0
    for entry in load_entries():
        if entry["id"] in ignore_ids:
            continue
        score = 0
        for keyword in entry["palavras_chave"]:
            k = _norm(keyword)
            # Aceita plural simples (impressora/impressoras) e exige palavra inteira.
            if k and re.search(rf"\b{re.escape(k)}(s|es)?\b", norm):
                score += len(k.split())  # expressões pesam mais que palavras soltas
        if score > best_score:
            best, best_score = entry, score
    return best


def format_solution(entry):
    """Texto (markdown) mostrado ao funcionário no chat."""
    steps = "\n".join(f"{i}. {s}" for i, s in enumerate(entry["passos"], start=1))
    text = (
        f"💡 **{entry['titulo']}**\n\n"
        "Esse é um problema que costuma ser resolvido com alguns passos simples. "
        "Tente na ordem abaixo:\n\n"
        f"{steps}\n"
    )
    if entry.get("resultado_esperado"):
        text += f"\n✔️ **O que deve acontecer:** {entry['resultado_esperado']}\n"
    text += "\nDepois de testar, me diga abaixo se resolveu."
    return text


def context_for_ai(entry):
    """Informa à IA o que o funcionário já tentou, para ela não repetir."""
    steps = "; ".join(f"{i}) {s}" for i, s in enumerate(entry["passos"], start=1))
    text = (
        f"CONTEXTO: o funcionário já recebeu e tentou o passo a passo \"{entry['titulo']}\": {steps}. "
        "Não repita esses passos. Pergunte o que aconteceu em cada etapa, sugira apenas "
        "verificações novas e simples e, se não houver mais nada seguro a tentar, "
        "encaminhe para a equipe de TI."
    )
    if entry.get("quando_abrir_chamado"):
        text += f" Critério da equipe de TI para abrir chamado: {entry['quando_abrir_chamado']}"
    return text


def ticket_description(entry, report):
    """Descrição do chamado aberto automaticamente quando o passo a passo não resolve."""
    steps = "\n".join(f"{i}. {s}" for i, s in enumerate(entry["passos"], start=1))
    return (
        "Chamado aberto automaticamente pelo TechAssist AI: o funcionário seguiu o passo a passo "
        f"\"{entry['titulo']}\" e o problema continuou.\n\n"
        f"Relato do funcionário: {report}\n\n"
        f"Passos já tentados:\n{steps}"
    )


# --- Intenção de encerrar a conversa (mensagens curtas digitadas no chat) ---
_RESOLVED = ["resolveu", "resolvido", "resolvi", "funcionou", "deu certo", "consegui",
             "voltou ao normal", "voltou a funcionar", "esta funcionando", "ja esta ok"]
_CLOSING = ["terminar conversa", "terminar a conversa", "terminar atendimento", "encerrar conversa",
            "encerrar a conversa", "encerrar atendimento", "encerrar chat", "finalizar conversa",
            "finalizar atendimento", "pode encerrar", "pode fechar", "pode finalizar", "tchau",
            "ate mais", "ate logo", "era so isso", "so isso", "nada mais", "obrigado", "obrigada",
            "brigado", "valeu"]
# Respostas à pergunta "Posso ajudar com mais algum problema?"
_NO_MORE = {"nao", "nao obrigado", "nao obrigada", "nao preciso", "nao preciso de mais nada",
            "nao tenho mais", "nada", "nenhum", "e so", "e so isso", "por enquanto e so"}
# Respostas à pergunta "Esse passo a passo resolveu?" quando é negativa
_NOT_RESOLVED = {"nao", "nao resolveu", "nao funcionou", "nao deu certo", "continua", "continua igual",
                 "ainda nao", "ainda nao resolveu", "continua com problema"}


def _has_phrase(norm, phrases):
    return any(re.search(rf"\b{re.escape(p)}\b", norm) for p in phrases)


def closing_intent(text, pending=False):
    """Detecta se uma mensagem curta quer encerrar a conversa.

    Retorna "resolvido", "encerrar", "nao_resolveu" (só com solução pendente) ou None.
    Perguntas e mensagens longas ou com negação seguem o fluxo normal, para não
    confundir "o sistema não encerra" (problema) com "encerrar conversa" (despedida).
    """
    raw = str(text)
    norm = _norm(raw)
    words = norm.split()
    if not words or "?" in raw:
        return None
    if pending and norm in _NOT_RESOLVED:
        return "nao_resolveu"
    if not pending and norm in _NO_MORE:
        return "encerrar"
    if len(words) > 8 or re.search(r"\b(nao|nem|ainda|continua|mas)\b", norm):
        return None
    if _has_phrase(norm, _RESOLVED):
        return "resolvido"
    if len(words) <= 5 and _has_phrase(norm, _CLOSING):
        return "encerrar"
    return None
