import secrets
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "techassist.db"

def connect():
    DB_PATH.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB_PATH)
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

def create_ticket(requester, title, category, priority, description):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with connect() as con:
        for _ in range(20):
            protocol = generate_protocol()
            try:
                con.execute(
                    """INSERT INTO tickets
                    (protocolo, solicitante, assunto, categoria, prioridade, descricao, status, criado_em, atualizado_em)
                    VALUES (?, ?, ?, ?, ?, ?, 'Aberto', ?, ?)""",
                    (protocol, requester, title, category, priority, description, now, now)
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

def update_ticket(protocol, status, note, author, priority=None):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with connect() as con:
        if priority is None:
            con.execute("UPDATE tickets SET status=?, atualizado_em=? WHERE protocolo=?", (status, now, protocol))
        else:
            con.execute("UPDATE tickets SET status=?, prioridade=?, atualizado_em=? WHERE protocolo=?", (status, priority, now, protocol))
        if note.strip():
            con.execute("INSERT INTO ticket_messages (protocolo, autor, mensagem, criado_em) VALUES (?, ?, ?, ?)",
                        (protocol, author, note.strip(), now))

def get_messages(protocol):
    with connect() as con:
        rows = con.execute("SELECT * FROM ticket_messages WHERE protocolo=? ORDER BY id", (protocol,)).fetchall()
        return [dict(r) for r in rows]
