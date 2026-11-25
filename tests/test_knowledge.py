"""Testes da base de soluções (knowledge.py e base_conhecimento.json).

Executar na pasta do projeto:  python -m unittest discover -s tests -v
"""
import json
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
import knowledge as kb  # noqa: E402

CATEGORIAS = {
    "Computador / Windows", "Linux", "Rede / Internet", "Acesso / Sistemas",
    "Impressora / Periféricos", "Servidor / Active Directory",
    "Firewall / pfSense", "Telefonia / Issabel / MicroSIP", "Outro",
}


class BuscaDeSolucoes(unittest.TestCase):
    CASOS = {
        "Estou sem internet": "sem-internet",
        "a impressora não imprime": "impressora",
        "esqueci minha senha": "nao-consigo-entrar",
        "meu mouse parou de funcionar": "teclado-mouse",
        "o excel travou de novo": "computador-lento-travado",
        "não consigo ligar pelo microsip": "ramal-telefone",
        "não consigo abrir a pasta de rede do financeiro": "pasta-de-rede",
        "o site do banco está bloqueado": "site-bloqueado",
        "meu pc não liga": "computador-nao-liga",
        "o outlook não envia email": "email",
        "sem som na reunião": "sem-som",
        "tela preta no monitor": "monitor-sem-imagem",
    }

    def test_frases_comuns_encontram_a_solucao_certa(self):
        for frase, esperado in self.CASOS.items():
            with self.subTest(frase=frase):
                achada = kb.find_solution(frase)
                self.assertIsNotNone(achada)
                self.assertEqual(achada["id"], esperado)

    def test_plural_e_acentos_sao_ignorados(self):
        self.assertEqual(kb.find_solution("As IMPRESSORAS não IMPRIMEM")["id"], "impressora")

    def test_mensagem_sem_relacao_nao_encontra_nada(self):
        self.assertIsNone(kb.find_solution("bom dia, preciso de ajuda"))
        self.assertIsNone(kb.find_solution("   "))

    def test_solucao_ja_sugerida_e_ignorada(self):
        self.assertIsNone(kb.find_solution("estou sem internet", ignore_ids=["sem-internet"]))

    def test_texto_formatado_tem_passos_numerados(self):
        texto = kb.format_solution(kb.get_entry("impressora"))
        self.assertIn("1. ", texto)
        self.assertIn("resolveu", texto.lower())

    def test_descricao_do_chamado_automatico(self):
        entrada = kb.get_entry("sem-internet")
        texto = kb.ticket_description(entrada, "estou sem internet")
        self.assertIn("estou sem internet", texto)
        self.assertIn(entrada["passos"][0], texto)


class IntegridadeDoJson(unittest.TestCase):
    def setUp(self):
        self.entradas = json.loads((RAIZ / "base_conhecimento.json").read_text(encoding="utf-8"))["entradas"]

    def test_ids_unicos(self):
        ids = [e["id"] for e in self.entradas]
        self.assertEqual(len(ids), len(set(ids)))

    def test_campos_obrigatorios_e_categoria_valida(self):
        for e in self.entradas:
            with self.subTest(entrada=e["id"]):
                self.assertTrue(e["titulo"].strip())
                self.assertGreaterEqual(len(e["palavras_chave"]), 1)
                self.assertGreaterEqual(len(e["passos"]), 3)
                self.assertIn(e.get("categoria_chamado", "Outro"), CATEGORIAS)


class IntencaoDeEncerramento(unittest.TestCase):
    # (mensagem, há solução/pergunta pendente?, resultado esperado)
    CASOS = [
        ("terminar conversa", True, "encerrar"),
        ("terminar conversa", False, "encerrar"),
        ("Tchau!", True, "encerrar"),
        ("obrigado", True, "encerrar"),
        ("Obrigado, resolveu", True, "resolvido"),
        ("funcionou, valeu", True, "resolvido"),
        ("consegui acessar o sistema", False, "resolvido"),
        ("pode encerrar o atendimento", True, "encerrar"),
        ("não", True, "nao_resolveu"),
        ("não funcionou", True, "nao_resolveu"),
        ("continua igual", True, "nao_resolveu"),
        ("ainda não", True, "nao_resolveu"),
        ("não", False, "encerrar"),
        ("Não, obrigado", False, "encerrar"),
        ("só isso", False, "encerrar"),
        ("nada", False, "encerrar"),
        # Não podem ser tratadas como despedida:
        ("o sistema não encerra", False, None),
        ("não consigo finalizar a venda", False, None),
        ("obrigado, mas agora a impressora não imprime", False, None),
        ("obrigado, e a impressora?", False, None),
        ("a impressora não imprime", False, None),
        ("estou sem internet", False, None),
    ]

    def test_casos(self):
        for texto, pendente, esperado in self.CASOS:
            with self.subTest(texto=texto, pendente=pendente):
                self.assertEqual(kb.closing_intent(texto, pending=pendente), esperado)


if __name__ == "__main__":
    unittest.main()
