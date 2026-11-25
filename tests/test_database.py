"""Testes do banco de dados (database.py) usando um arquivo temporário.

Executar na pasta do projeto:  python -m unittest discover -s tests -v
"""
import re
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import database as db  # noqa: E402


class BancoTemporario(unittest.TestCase):
    def setUp(self):
        self._pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self._pasta.cleanup)
        db.DB_PATH = Path(self._pasta.name) / "teste.db"
        db.init_db()


class CodigoDoChamado(BancoTemporario):
    def test_formato_8_caracteres_com_letra_e_numero(self):
        for _ in range(500):
            codigo = db.generate_protocol()
            self.assertRegex(codigo, r"^[A-Z0-9]{8}$")
            self.assertTrue(re.search(r"\d", codigo) and re.search(r"[A-Z]", codigo))
            self.assertFalse(set(codigo) & set("01OIL"))   # sem caracteres ambíguos

    def test_codigos_unicos_em_muitos_chamados(self):
        codigos = {db.create_ticket("Ana", f"assunto {i}", "Outro", "Média", "desc") for i in range(1000)}
        self.assertEqual(len(codigos), 1000)

    def test_colisao_sorteia_outro_codigo(self):
        sequencia = iter(["ABCD2345", "ABCD2345", "WXYZ6789"])
        original = db.generate_protocol
        db.generate_protocol = lambda length=8: next(sequencia)
        try:
            a = db.create_ticket("Bia", "x", "Outro", "Média", "d")
            b = db.create_ticket("Bia", "y", "Outro", "Média", "d")
        finally:
            db.generate_protocol = original
        self.assertEqual((a, b), ("ABCD2345", "WXYZ6789"))


class Chamados(BancoTemporario):
    def test_criacao_guarda_nome_setor_e_valores_iniciais(self):
        codigo = db.create_ticket("Maria Silva", "Sem internet", "Rede / Internet", "Média", "desc", sector="Clínica")
        t = db.list_tickets()[0]
        self.assertEqual((t["protocolo"], t["solicitante"], t["setor"]), (codigo, "Maria Silva", "Clínica"))
        self.assertEqual((t["status"], t["prioridade"]), ("Aberto", "Média"))

    def test_meus_chamados_ignora_maiusculas(self):
        db.create_ticket("Ana Souza", "a", "Outro", "Média", "d")
        db.create_ticket("Outra Pessoa", "b", "Outro", "Média", "d")
        self.assertEqual(len(db.list_tickets("ana souza")), 1)
        self.assertEqual(len(db.list_tickets("ANA SOUZA")), 1)
        self.assertEqual(len(db.list_tickets()), 2)

    def test_atualizacao_registra_status_prioridade_e_historico(self):
        codigo = db.create_ticket("Ana", "a", "Outro", "Média", "descrição inicial")
        db.update_ticket(codigo, "Em atendimento", "Reiniciei o roteador", "Técnico de TI", "Alta")
        t = db.list_tickets()[0]
        self.assertEqual((t["status"], t["prioridade"]), ("Em atendimento", "Alta"))
        autores = [m["autor"] for m in db.get_messages(codigo)]
        self.assertEqual(autores, ["Ana", "Técnico de TI"])


class EventosEMigracao(BancoTemporario):
    def test_estatisticas_de_autoatendimento(self):
        for resultado in ("sugerida", "sugerida", "resolveu", "nao_resolveu"):
            db.log_kb_event("sem-internet", "Ana", resultado)
        self.assertEqual(db.kb_stats(), {"sugerida": 2, "resolveu": 1, "nao_resolveu": 1})

    def test_banco_antigo_sem_coluna_setor_e_migrado(self):
        antigo = Path(self._pasta.name) / "antigo.db"
        con = sqlite3.connect(antigo)
        con.executescript("""
            CREATE TABLE tickets (id INTEGER PRIMARY KEY AUTOINCREMENT, protocolo TEXT UNIQUE, solicitante TEXT NOT NULL,
              assunto TEXT NOT NULL, categoria TEXT NOT NULL, prioridade TEXT NOT NULL, descricao TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'Aberto', criado_em TEXT NOT NULL, atualizado_em TEXT NOT NULL);
            CREATE TABLE ticket_messages (id INTEGER PRIMARY KEY AUTOINCREMENT, protocolo TEXT NOT NULL,
              autor TEXT NOT NULL, mensagem TEXT NOT NULL, criado_em TEXT NOT NULL);
            INSERT INTO tickets (protocolo, solicitante, assunto, categoria, prioridade, descricao, criado_em, atualizado_em)
              VALUES ('TI-00001', 'Carlos', 'antigo', 'Outro', 'Média', 'd', '2026-11-10', '2026-11-10');
        """)
        con.commit()
        con.close()
        db.DB_PATH = antigo
        db.init_db()
        db.init_db()   # rodar duas vezes não pode falhar
        db.create_ticket("Ana", "novo", "Outro", "Média", "d", sector="RH")
        setores = {t["protocolo"]: t["setor"] for t in db.list_tickets()}
        self.assertEqual(setores["TI-00001"], "")
        self.assertIn("RH", setores.values())


class ConversaNoChamado(BancoTemporario):
    def setUp(self):
        super().setUp()
        self.codigo = db.create_ticket("Ana Souza", "Sem internet", "Rede / Internet", "Média", "desc", sector="RH")

    def test_anotacao_interna_nao_aparece_para_o_funcionario(self):
        db.update_ticket(self.codigo, "Em atendimento", "Visível ao funcionário", "Técnico de TI", "Alta")
        db.update_ticket(self.codigo, "Em atendimento", "Só a TI vê", "Técnico de TI", "Alta", internal=True)
        todas = [m["mensagem"] for m in db.get_messages(self.codigo)]
        visiveis = [m["mensagem"] for m in db.get_messages(self.codigo, include_internal=False)]
        self.assertIn("Só a TI vê", todas)
        self.assertNotIn("Só a TI vê", visiveis)
        self.assertIn("Visível ao funcionário", visiveis)

    def test_resposta_do_funcionario_reabre_chamado_aguardando_ou_resolvido(self):
        for status_inicial in ("Aguardando usuário", "Resolvido"):
            with self.subTest(status=status_inicial):
                db.update_ticket(self.codigo, status_inicial, "", "Técnico de TI")
                self.assertEqual(db.add_reply(self.codigo, "ana souza", "Continua igual"), "Em atendimento")
        self.assertEqual(db.get_messages(self.codigo)[-1]["autor"], "ana souza")

    def test_resposta_mantem_outros_status(self):
        db.update_ticket(self.codigo, "Aberto", "", "Técnico de TI")
        self.assertEqual(db.add_reply(self.codigo, "Ana Souza", "Mais um detalhe"), "Aberto")

    def test_resposta_so_do_dono_e_nao_em_chamado_fechado(self):
        with self.assertRaises(ValueError):
            db.add_reply(self.codigo, "Outra Pessoa", "Tentando mexer")
        db.update_ticket(self.codigo, "Fechado", "", "Técnico de TI")
        with self.assertRaises(ValueError):
            db.add_reply(self.codigo, "Ana Souza", "Depois de fechar")


class LacunasBackupELogin(BancoTemporario):
    def test_lacunas_contam_repeticoes_ignoram_curtas_e_nao_guardam_nome(self):
        for texto in ("o sistema de notas esta fora do ar", "O sistema de notas esta fora do ar", "oi", "   "):
            db.log_gap(texto)
        db.log_gap("preciso configurar a assinatura do e-mail")
        lacunas = db.list_gaps()
        self.assertEqual(lacunas[0]["vezes"], 2)
        self.assertEqual(len(lacunas), 2)
        self.assertEqual(set(lacunas[0]), {"texto", "vezes", "ultima"})   # nenhum campo com nome de pessoa

    def test_backup_e_um_banco_valido_com_os_chamados(self):
        codigo = db.create_ticket("Ana", "a", "Outro", "Média", "d", sector="RH")
        copia = Path(self._pasta.name) / "copia.db"
        copia.write_bytes(db.backup_bytes())
        con = sqlite3.connect(copia)
        self.addCleanup(con.close)
        self.assertEqual(con.execute("SELECT protocolo FROM tickets").fetchone()[0], codigo)

    def test_contador_de_falhas_de_login(self):
        db.reset_login_failures()
        self.assertEqual([db.register_login_failure() for _ in range(3)], [1, 2, 3])
        db.reset_login_failures()
        self.assertEqual(db.register_login_failure(), 1)

    def test_banco_antigo_sem_coluna_interna_e_migrado(self):
        antigo = Path(self._pasta.name) / "antigo2.db"
        con = sqlite3.connect(antigo)
        con.executescript("""
            CREATE TABLE ticket_messages (id INTEGER PRIMARY KEY AUTOINCREMENT, protocolo TEXT NOT NULL,
              autor TEXT NOT NULL, mensagem TEXT NOT NULL, criado_em TEXT NOT NULL);
            INSERT INTO ticket_messages (protocolo, autor, mensagem, criado_em) VALUES ('TI-00001', 'Carlos', 'oi', '2026-11-10');
        """)
        con.commit()
        con.close()
        db.DB_PATH = antigo
        db.init_db()
        db.init_db()
        self.assertEqual(db.get_messages("TI-00001", include_internal=False)[0]["mensagem"], "oi")


if __name__ == "__main__":
    unittest.main()
