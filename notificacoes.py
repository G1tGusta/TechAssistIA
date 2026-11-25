"""Avisos para a equipe de TI: e-mail (SMTP), Microsoft Teams e webhook de texto.

Tudo é configurado no arquivo .env e é opcional: sem nenhum canal configurado, nada é enviado.

  URL_DO_SISTEMA          endereço do sistema, para o link nos avisos (ex.: http://servidor:8501)
  NOTIFICAR_EMAIL_PARA    destinatários separados por vírgula (usa SMTP_*)
  SMTP_HOST, SMTP_PORT (587), SMTP_USER, SMTP_PASSWORD, SMTP_FROM,
  SMTP_SEGURANCA          starttls (padrão), ssl ou nenhuma
  NOTIFICAR_TEAMS_URL     URL do webhook de um fluxo de trabalho (Workflows) do Teams
  NOTIFICAR_WEBHOOK_URL   webhook genérico que recebe {"text": "..."} (Slack, Google Chat, Mattermost...)

Os envios acontecem em segundo plano: uma falha de rede nunca atrapalha o funcionário.
"""
import json
import os
import smtplib
import ssl
import threading
import urllib.request
from email.message import EmailMessage

TIMEOUT = 10          # segundos de espera por canal
LIMITE_TEXTO = 500    # caracteres da descrição enviados no aviso


def _env(nome, padrao=""):
    return os.getenv(nome, padrao).strip()


def canais_configurados():
    canais = []
    if _env("SMTP_HOST") and _env("NOTIFICAR_EMAIL_PARA"):
        canais.append("E-mail")
    if _env("NOTIFICAR_TEAMS_URL"):
        canais.append("Microsoft Teams")
    if _env("NOTIFICAR_WEBHOOK_URL"):
        canais.append("Webhook (texto)")
    return canais


def _cortar(texto, limite=LIMITE_TEXTO):
    texto = " ".join(str(texto).split())
    return texto if len(texto) <= limite else texto[: limite - 1] + "…"


def montar_mensagem(evento):
    """Devolve (título, [(rótulo, valor), ...], corpo, url) para o evento."""
    tipo = evento.get("tipo")
    protocolo = evento.get("protocolo", "")
    if tipo == "novo":
        titulo = f"Novo chamado {protocolo}: {_cortar(evento.get('assunto', ''), 80)}"
        corpo = _cortar(evento.get("descricao", ""))
    elif tipo == "resposta":
        titulo = f"Resposta do funcionário no chamado {protocolo}"
        corpo = _cortar(evento.get("mensagem", ""))
    else:
        titulo = "Teste de aviso do TechAssist AI"
        corpo = "Se você recebeu esta mensagem, este canal está configurado corretamente."
    fatos = [("Protocolo", protocolo), ("Funcionário", evento.get("solicitante", "")),
             ("Setor", evento.get("setor", "") or "—")]
    if evento.get("assunto") and tipo == "resposta":
        fatos.append(("Assunto", _cortar(evento["assunto"], 80)))
    if tipo == "novo":
        fatos += [("Categoria", evento.get("categoria", "")), ("Prioridade", evento.get("prioridade", ""))]
    fatos = [(k, v) for k, v in fatos if v]
    if tipo == "teste":
        fatos = []
    return titulo, fatos, corpo, _env("URL_DO_SISTEMA")


def _texto_simples(titulo, fatos, corpo, url):
    linhas = [titulo] + [f"{k}: {v}" for k, v in fatos]
    if corpo:
        linhas += ["", corpo]
    if url:
        linhas += ["", f"Abrir o sistema: {url}"]
    return "\n".join(linhas)


def _enviar_email(titulo, fatos, corpo, url):
    destinos = [e.strip() for e in _env("NOTIFICAR_EMAIL_PARA").split(",") if e.strip()]
    usuario = _env("SMTP_USER")
    msg = EmailMessage()
    msg["Subject"] = f"[TechAssist] {titulo}"
    msg["From"] = _env("SMTP_FROM") or usuario or "techassist@localhost"
    msg["To"] = ", ".join(destinos)
    msg.set_content(_texto_simples(titulo, fatos, corpo, url))
    porta = int(_env("SMTP_PORT") or 587)
    seguranca = (_env("SMTP_SEGURANCA") or "starttls").lower()
    if seguranca == "ssl":
        servidor = smtplib.SMTP_SSL(_env("SMTP_HOST"), porta, timeout=TIMEOUT, context=ssl.create_default_context())
    else:
        servidor = smtplib.SMTP(_env("SMTP_HOST"), porta, timeout=TIMEOUT)
    with servidor:
        if seguranca == "starttls":
            servidor.starttls(context=ssl.create_default_context())
        if usuario:
            servidor.login(usuario, _env("SMTP_PASSWORD"))
        servidor.send_message(msg)


def _post_json(url, carga):
    req = urllib.request.Request(
        url, data=json.dumps(carga).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT):
        pass  # qualquer resposta 2xx é sucesso; erros viram exceção


def _enviar_teams(titulo, fatos, corpo, url):
    cartao = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {"type": "TextBlock", "text": titulo, "weight": "Bolder", "size": "Medium", "wrap": True},
            *([{"type": "FactSet", "facts": [{"title": k, "value": str(v)} for k, v in fatos]}] if fatos else []),
            *([{"type": "TextBlock", "text": corpo, "wrap": True}] if corpo else []),
        ],
    }
    if url:
        cartao["actions"] = [{"type": "Action.OpenUrl", "title": "Abrir o TechAssist AI", "url": url}]
    # "attachments" serve ao modelo de fluxo que recebe cartão; "text" serve ao fluxo em branco.
    _post_json(_env("NOTIFICAR_TEAMS_URL"), {
        "type": "message",
        "text": _texto_simples(titulo, fatos, corpo, url),
        "attachments": [{"contentType": "application/vnd.microsoft.card.adaptive",
                         "contentUrl": None, "content": cartao}],
    })


def _enviar_webhook(titulo, fatos, corpo, url):
    _post_json(_env("NOTIFICAR_WEBHOOK_URL"), {"text": _texto_simples(titulo, fatos, corpo, url)})


def enviar_agora(evento):
    """Envia para todos os canais configurados e devolve {canal: 'ok' ou 'erro: ...'}."""
    mensagem = montar_mensagem(evento)
    envios = {"E-mail": _enviar_email, "Microsoft Teams": _enviar_teams, "Webhook (texto)": _enviar_webhook}
    resultado = {}
    for canal in canais_configurados():
        try:
            envios[canal](*mensagem)
            resultado[canal] = "ok"
        except Exception as exc:   # um canal com problema não pode impedir os outros
            resultado[canal] = f"erro: {exc}"
    return resultado


def _em_segundo_plano(evento):
    for canal, status in enviar_agora(evento).items():
        if status != "ok":
            print(f"[TechAssist] Aviso por {canal} não enviado ({status})")


def notificar(evento):
    """Dispara o aviso sem esperar (não trava a tela do funcionário)."""
    if canais_configurados():
        threading.Thread(target=_em_segundo_plano, args=(evento,), daemon=True).start()


def notificar_novo_chamado(protocolo, solicitante, setor, assunto, categoria, prioridade, descricao):
    notificar({"tipo": "novo", "protocolo": protocolo, "solicitante": solicitante, "setor": setor,
               "assunto": assunto, "categoria": categoria, "prioridade": prioridade, "descricao": descricao})


def notificar_resposta(protocolo, solicitante, setor, assunto, mensagem):
    notificar({"tipo": "resposta", "protocolo": protocolo, "solicitante": solicitante, "setor": setor,
               "assunto": assunto, "mensagem": mensagem})


def enviar_teste():
    return enviar_agora({"tipo": "teste"})
