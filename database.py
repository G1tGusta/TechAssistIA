import os
import secrets
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

try:  # permite definir TECHASSIST_DB no arquivo .env
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Por padrão o banco fica em data/techassist.db. Em servidor ou Docker, defina TECHASSIST_DB
# com o caminho completo do arquivo (ex.: /data/techassist.db).
DB_PATH = Path(os.getenv("TECHASSIST_DB", "").strip() or Path(__file__).parent / "data" / "techassist.db")

def connect():
    DB_PATH.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=10)   # espera até 10 s se outro usuário estiver gravando
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with connect() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                protocolo TEXT UNIQUE,
                solicitante TEXT NOT NULL,
                assunto TEXT NOT NULL,
                categoria TEXT NOT NULL,
                prioridade TEXT NOT NULL,
                descricao TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Aberto',
                criado_em TEXT NOT NULL,
                atualizado_em TEXT NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS ticket_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                protocolo TEXT NOT NULL,
                autor TEXT NOT NULL,
                mensagem TEXT NOT NULL,
                criado_em TEXT NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS kb_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entrada_id TEXT NOT NULL,
                solicitante TEXT NOT NULL,
                resultado TEXT NOT NULL,
                criado_em TEXT NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS kb_gaps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                texto TEXT NOT NULL,
                criado_em TEXT NOT NULL
            )
        """)
        # Bancos criados em versões anteriores: acrescenta colunas novas.
        cols = [r["name"] for r in con.execute("PRAGMA table_info(tickets)")]
        if "setor" not in cols:
            con.execute("ALTER TABLE tickets ADD COLUMN setor TEXT NOT NULL DEFAULT ''")
        mcols = [r["name"] for r in con.execute("PRAGMA table_info(ticket_messages)")]
        if "interna" not in mcols:
            con.execute("ALTER TABLE ticket_messages ADD COLUMN interna INTEGER NOT NULL DEFAULT 0")

def log_kb_event(entry_id, requester, result):
    """Registra uso da base de soluções: sugerida, resolveu ou nao_resolveu."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with connect() as con:
        con.execute("INSERT INTO kb_events (entrada_id, solicitante, resultado, criado_em) VALUES (?, ?, ?, ?)",
                    (entry_id, requester, result, now))

def kb_stats():
    with connect() as con:
        rows = con.execute("SELECT resultado, COUNT(*) AS total FROM kb_events GROUP BY resultado").fetchall()
        return {r["resultado"]: r["total"] for r in rows}

# Alfabeto do código do chamado: sem 0/O, 1/I/L, que se confundem na hora de ditar ou digitar.
_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"

def generate_protocol(length=8):
    """Código aleatório de até 8 caracteres, sempre com pelo menos uma letra e um número."""
    while True:
        code = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(length))
        if any(c.isdigit() for c in code) and any(c.isalpha() for c in code):
            return code

def create_ticket(requester, title, category, priority, description, sector=""):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with connect() as con:
        for _ in range(20):
            protocol = generate_protocol()
            try:
                con.execute(
                    """INSERT INTO tickets
                    (protocolo, solicitante, setor, assunto, categoria, prioridade, descricao, status, criado_em, atualizado_em)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'Aberto', ?, ?)""",
                    (protocol, requester, sector, title, category, priority, description, now, now)
                )
                break
            except sqlite3.IntegrityError:
                continue  # código já existe: sorteia outro
        else:
            raise RuntimeError("Não foi possível gerar um código de chamado único.")
        con.execute("INSERT INTO ticket_messages (protocolo, autor, mensagem, criado_em) VALUES (?, ?, ?, ?)",
                    (protocol, requester, "Chamado aberto: " + description, now))
        return protocol

def list_tickets(requester=None):
    with connect() as con:
        if requester:
            rows = con.execute("SELECT * FROM tickets WHERE solicitante=? COLLATE NOCASE ORDER BY id DESC", (requester,)).fetchall()
        else:
            rows = con.execute("SELECT * FROM tickets ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]

def update_ticket(protocol, status, note, author, priority=None, internal=False):
    """Atualiza status/prioridade e, se houver anotação, grava no histórico.
    Anotação interna (internal=True) fica visível só para a equipe de TI."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with connect() as con:
        if priority is None:
            con.execute("UPDATE tickets SET status=?, atualizado_em=? WHERE protocolo=?", (status, now, protocol))
        else:
            con.execute("UPDATE tickets SET status=?, prioridade=?, atualizado_em=? WHERE protocolo=?", (status, priority, now, protocol))
        if note.strip():
            con.execute("INSERT INTO ticket_messages (protocolo, autor, mensagem, criado_em, interna) VALUES (?, ?, ?, ?, ?)",
                        (protocol, author, note.strip(), now, 1 if internal else 0))

def get_messages(protocol, include_internal=True):
    """Histórico do chamado em ordem cronológica. O funcionário usa include_internal=False."""
    sql = "SELECT * FROM ticket_messages WHERE protocolo=?"
    if not include_internal:
        sql += " AND interna=0"
    with connect() as con:
        rows = con.execute(sql + " ORDER BY id", (protocol,)).fetchall()
        return [dict(r) for r in rows]

def add_reply(protocol, author, text):
    """Mensagem do funcionário em um chamado dele. Se a TI estava aguardando ou o chamado
    estava resolvido, volta para 'Em atendimento'. Retorna o status resultante."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with connect() as con:
        row = con.execute("SELECT status FROM tickets WHERE protocolo=? AND solicitante=? COLLATE NOCASE",
                          (protocol, author)).fetchone()
        if row is None:
            raise ValueError("Chamado não encontrado para este solicitante.")
        if row["status"] == "Fechado":
            raise ValueError("Chamado fechado: abra um novo chamado.")
        status = "Em atendimento" if row["status"] in ("Aguardando usuário", "Resolvido") else row["status"]
        con.execute("INSERT INTO ticket_messages (protocolo, autor, mensagem, criado_em, interna) VALUES (?, ?, ?, ?, 0)",
                    (protocol, author, text.strip(), now))
        con.execute("UPDATE tickets SET status=?, atualizado_em=? WHERE protocolo=?", (status, now, protocol))
        return status

def log_gap(text):
    """Guarda (sem o nome de quem escreveu) uma mensagem que a base não soube responder,
    para a TI decidir quais soluções criar."""
    text = " ".join(str(text).split())[:200]
    if len(text) < 10:
        return
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with connect() as con:
        con.execute("INSERT INTO kb_gaps (texto, criado_em) VALUES (?, ?)", (text, now))

def list_gaps(limit=30):
    with connect() as con:
        rows = con.execute(
            "SELECT texto, COUNT(*) AS vezes, MAX(criado_em) AS ultima FROM kb_gaps "
            "GROUP BY LOWER(texto) ORDER BY vezes DESC, ultima DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

def backup_bytes():
    """Cópia consistente do banco inteiro (pode ser feita com o sistema em uso)."""
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "backup.db"
        src = connect()
        dst = sqlite3.connect(dest)
        try:
            src.backup(dst)
        finally:
            dst.close()
            src.close()
        return dest.read_bytes()

# Falhas seguidas de senha do técnico. Este módulo fica na memória enquanto o sistema está
# ligado (o app.py é reexecutado a cada clique), então o contador vale para todas as sessões.
_login_failures = {"n": 0}

def register_login_failure():
    _login_failures["n"] += 1
    return _login_failures["n"]

def reset_login_failures():
    _login_failures["n"] = 0
