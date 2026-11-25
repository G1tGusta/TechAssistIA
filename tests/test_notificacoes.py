"""Testes dos avisos para a TI (notificacoes.py), sem rede: SMTP e HTTP são simulados.

Executar na pasta do projeto:  python -m unittest discover -s tests -v
"""
import json
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import notificacoes as nt  # noqa: E402

VARIAVEIS = ["URL_DO_SISTEMA", "NOTIFICAR_EMAIL_PARA", "SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD",
             "SMTP_FROM", "SMTP_SEGURANCA", "NOTIFICAR_TEAMS_URL", "NOTIFICAR_WEBHOOK_URL"]
NOVO = {"tipo": "novo", "protocolo": "K7M2X9QA", "solicitante": "Maria Silva", "setor": "Clínica",
        "assunto": "Sem internet", "categoria": "Rede / Internet", "prioridade": "Média",
        "descricao": "Estou sem internet desde cedo"}


class Base(unittest.TestCase):
    def configurar(self, **env):
        limpo = {k: v for k, v in os.environ.items() if k not in VARIAVEIS}
        limpo.update(env)
        patcher = mock.patch.dict(os.environ, limpo, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)


class SemCanais(Base):
    def test_sem_configuracao_nada_e_enviado(self):
        self.configurar()
        self.assertEqual(nt.canais_configurados(), [])
        with mock.patch.object(nt.threading, "Thread") as thread:
            nt.notificar_novo_chamado("K7M2X9QA", "Ana", "RH", "a", "Outro", "Média", "d")
            thread.assert_not_called()

    def test_email_exige_host_e_destinatario(self):
        self.configurar(SMTP_HOST="smtp.exemplo.com")
        self.assertEqual(nt.canais_configurados(), [])
        self.configurar(SMTP_HOST="smtp.exemplo.com", NOTIFICAR_EMAIL_PARA="ti@exemplo.com")
        self.assertEqual(nt.canais_configurados(), ["E-mail"])


class Email(Base):
    def test_starttls_login_e_conteudo(self):
        self.configurar(SMTP_HOST="smtp.exemplo.com", NOTIFICAR_EMAIL_PARA="a@x.com, b@x.com", SMTP_USER="robo@x.com",
                        SMTP_PASSWORD="segredo", URL_DO_SISTEMA="http://servidor:8501")
        with mock.patch.object(nt.smtplib, "SMTP") as smtp:
            servidor = smtp.return_value
            servidor.__enter__.return_value = servidor
            self.assertEqual(nt.enviar_agora(NOVO), {"E-mail": "ok"})
        smtp.assert_called_once_with("smtp.exemplo.com", 587, timeout=nt.TIMEOUT)
        servidor.starttls.assert_called_once()
        servidor.login.assert_called_once_with("robo@x.com", "segredo")
        msg = servidor.send_message.call_args[0][0]
        self.assertEqual(msg["To"], "a@x.com, b@x.com")
        self.assertEqual(msg["From"], "robo@x.com")
        self.assertIn("K7M2X9QA", msg["Subject"])
        corpo = msg.get_content()
        for trecho in ("Maria Silva", "Clínica", "Rede / Internet", "Estou sem internet", "http://servidor:8501"):
            self.assertIn(trecho, corpo)

    def test_modo_ssl_usa_smtp_ssl_e_nao_starttls(self):
        self.configurar(SMTP_HOST="smtp.exemplo.com", NOTIFICAR_EMAIL_PARA="a@x.com", SMTP_SEGURANCA="ssl", SMTP_PORT="465")
        with mock.patch.object(nt.smtplib, "SMTP_SSL") as smtp_ssl:
            servidor = smtp_ssl.return_value
            servidor.__enter__.return_value = servidor
            self.assertEqual(nt.enviar_agora(NOVO), {"E-mail": "ok"})
        self.assertEqual(smtp_ssl.call_args[0][:2], ("smtp.exemplo.com", 465))
        servidor.starttls.assert_not_called()
        servidor.login.assert_not_called()   # sem SMTP_USER, não tenta login


class Webhooks(Base):
    def _capturar(self):
        enviados = []

        def falso(req, timeout=None):
            enviados.append(req)
            return mock.MagicMock()
        return enviados, falso

    def test_teams_envia_cartao_e_texto(self):
        self.configurar(NOTIFICAR_TEAMS_URL="https://teams.exemplo/webhook", URL_DO_SISTEMA="http://servidor:8501")
        enviados, falso = self._capturar()
        with mock.patch.object(nt.urllib.request, "urlopen", falso):
            self.assertEqual(nt.enviar_agora(NOVO), {"Microsoft Teams": "ok"})
        req = enviados[0]
        self.assertEqual((req.full_url, req.get_method()), ("https://teams.exemplo/webhook", "POST"))
        self.assertIn("application/json", req.get_header("Content-type"))
        carga = json.loads(req.data.decode("utf-8"))
        self.assertEqual(carga["type"], "message")
        self.assertIn("K7M2X9QA", carga["text"])
        anexo = carga["attachments"][0]
        self.assertEqual(anexo["contentType"], "application/vnd.microsoft.card.adaptive")
        cartao = anexo["content"]
        self.assertEqual(cartao["type"], "AdaptiveCard")
        fatos = {f["title"]: f["value"] for f in cartao["body"][1]["facts"]}
        self.assertEqual(fatos["Setor"], "Clínica")
        self.assertEqual(cartao["actions"][0]["url"], "http://servidor:8501")

    def test_webhook_generico_envia_texto(self):
        self.configurar(NOTIFICAR_WEBHOOK_URL="https://chat.exemplo/hook")
        enviados, falso = self._capturar()
        with mock.patch.object(nt.urllib.request, "urlopen", falso):
            self.assertEqual(nt.enviar_agora(NOVO), {"Webhook (texto)": "ok"})
        carga = json.loads(enviados[0].data.decode("utf-8"))
        self.assertEqual(set(carga), {"text"})
        self.assertIn("Sem internet", carga["text"])


class Robustez(Base):
    def test_falha_em_um_canal_nao_impede_os_outros_nem_gera_excecao(self):
        self.configurar(NOTIFICAR_TEAMS_URL="https://teams.exemplo/webhook", NOTIFICAR_WEBHOOK_URL="https://chat.exemplo/hook")
        chamadas = []

        def falso(req, timeout=None):
            chamadas.append(req.full_url)
            if "teams" in req.full_url:
                raise OSError("sem rede")
            return mock.MagicMock()
        with mock.patch.object(nt.urllib.request, "urlopen", falso):
            resultado = nt.enviar_agora(NOVO)
        self.assertTrue(resultado["Microsoft Teams"].startswith("erro:"))
        self.assertEqual(resultado["Webhook (texto)"], "ok")
        self.assertEqual(len(chamadas), 2)

    def test_descricao_longa_e_cortada(self):
        titulo, fatos, corpo, url = nt.montar_mensagem(dict(NOVO, descricao="palavra " * 400))
        self.assertLessEqual(len(corpo), nt.LIMITE_TEXTO)
        self.assertTrue(corpo.endswith("…"))

    def test_notificar_dispara_em_segundo_plano(self):
        self.configurar(NOTIFICAR_WEBHOOK_URL="https://chat.exemplo/hook")
        with mock.patch.object(nt.threading, "Thread") as thread, mock.patch.object(nt, "enviar_agora") as enviar:
            thread.side_effect = lambda target, args, daemon: SimpleNamespace(start=lambda: target(*args))
            nt.notificar_resposta("K7M2X9QA", "Ana", "RH", "Sem internet", "Continua igual")
        evento = enviar.call_args[0][0]
        self.assertEqual((evento["tipo"], evento["mensagem"]), ("resposta", "Continua igual"))

    def test_mensagem_de_teste(self):
        titulo, fatos, corpo, url = nt.montar_mensagem({"tipo": "teste"})
        self.assertIn("Teste", titulo)
        self.assertEqual(fatos, [])


if __name__ == "__main__":
    unittest.main()
