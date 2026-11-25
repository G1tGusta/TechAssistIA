# Implantação em servidor único e avisos para a TI

> **PARA DEPOIS.** Este guia não é necessário para usar o sistema no seu computador. Use-o quando for transferir para o servidor.
> Versão do documento: acompanha o TechAssist AI 1.1.1.

## 1. Por que um servidor só

Cada computador que executa o sistema tem o **seu próprio banco de dados**. Para que todos os funcionários abram
chamados no mesmo lugar e a TI veja tudo junto, o sistema roda em **um único computador ou servidor**, e os
funcionários acessam pelo navegador: `http://ENDEREÇO-DO-SERVIDOR:8501`.

Escolha um dos três jeitos de colocar no ar (use só um):

| Jeito | Quando usar |
|---|---|
| A) Windows | A TI já tem um PC ou servidor Windows ligado o dia todo |
| B) Linux (systemd) | Existe um servidor Linux |
| C) Docker | A TI já usa Docker; é o jeito mais isolado e fácil de atualizar |

Em todos: o servidor precisa de **endereço fixo** (IP fixo ou nome na rede) e da **porta 8501** liberada na rede interna.
Não exponha a porta na internet.

## 2. A) Windows

1. Instale o Python 3.10 ou superior (python.org), marcando **Add python.exe to PATH**.
2. Copie a pasta do projeto para o servidor (por exemplo `C:\TechAssist`), **sem** `.venv` e **sem** `.env`.
3. Dê dois cliques em `IniciarTechAssist.bat`. Ele instala tudo e abre o `.env`: preencha `TECHNICIAN_PASSWORD`,
   `GROQ_API_KEY` (se usar a IA) e `URL_DO_SISTEMA` (ex.: `http://servidor-ti:8501`). Feche a janela depois de ver o sistema abrir.
4. Teste o modo servidor: dê dois cliques em `servidor\IniciarServidor.bat` e, de outro computador, abra `http://IP-DO-SERVIDOR:8501`.
5. Para iniciar sozinho com o Windows: clique com o botão direito em `servidor\InstalarServicoWindows.bat` > **Executar como administrador**.
   Ele cria a tarefa agendada `TechAssistAI` (inicia com o Windows) e libera a porta 8501 nas redes privada e de domínio.
6. Para remover: `servidor\RemoverServicoWindows.bat`, também como administrador.

Observações: a tarefa não reinicia o sistema se ele fechar sozinho (reiniciar o computador resolve). Para ver mensagens de
erro, rode `servidor\IniciarServidor.bat` manualmente. Para reinício automático em caso de falha, use um gerenciador de serviços como o NSSM.

## 3. B) Linux (systemd)

```
sudo useradd --system --create-home --home-dir /opt/techassist techassist
sudo cp -r TechAssistAI/. /opt/techassist/          # sem .venv e sem .env
sudo chown -R techassist: /opt/techassist
sudo -u techassist /opt/techassist/IniciarTechAssist.sh     # prepara o ambiente e cria o .env
sudo -u techassist nano /opt/techassist/.env                # preencha as variáveis
sudo cp /opt/techassist/servidor/techassist.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now techassist
sudo systemctl status techassist                            # logs: journalctl -u techassist -f
```

No Debian/Ubuntu, se o ambiente virtual falhar: `sudo apt install python3-venv`.

## 4. C) Docker

Pré-requisito: Docker com o plugin Compose.

```
cp .env.example .env        # preencha TECHNICIAN_PASSWORD, GROQ_API_KEY, URL_DO_SISTEMA...
cd servidor
docker compose up -d --build
docker compose logs -f      # ver mensagens
```

- Os chamados ficam na pasta `dados/` da raiz do projeto (volume). **Faça backup dessa pasta.**
- `base_conhecimento.json` é montado de fora: edite o arquivo e a mudança vale sem reconstruir.
- O contêiner usa o horário de Brasília (`TZ=America/Sao_Paulo`) e tem verificação de saúde (`docker ps` mostra *healthy*).
- Atualizar: substitua os arquivos do projeto e rode `docker compose up -d --build` dentro da pasta `servidor`. O banco em `dados/` é preservado.

## 5. HTTPS (recomendado)

Por HTTP simples, o nome do funcionário e a senha do técnico trafegam sem criptografia. Coloque um proxy reverso na frente:
veja `servidor/Caddyfile.exemplo` (mais simples) ou `servidor/nginx.conf.exemplo`. O Streamlit usa WebSocket; os exemplos já
tratam isso. Com HTTPS, feche a porta 8501 para a rede e deixe só a 443.

## 6. Avisos para a TI (e-mail, Teams, webhook)

O sistema avisa a TI quando **nasce um chamado** (manual, automático ou pela conversa com a IA) e quando o **funcionário
responde** em um chamado. Os avisos saem em segundo plano: se um canal falhar, o funcionário nem percebe, e o motivo aparece
na janela/log do sistema. Todos os canais são opcionais e podem ser usados juntos.

O aviso leva: protocolo, nome, setor, assunto, categoria, prioridade e até 500 caracteres do relato. Esses dados saem do
sistema para o Teams ou para o e-mail: configure só canais aprovados pela empresa.

### Microsoft Teams

O Teams recebe avisos por **fluxo de trabalho (Workflows)**; os antigos webhooks de conector do Office 365 foram descontinuados.

1. No Teams, abra o canal onde a TI quer receber os avisos > **...** > **Workflows**.
2. Escolha o modelo de **webhook** (por exemplo, enviar alertas de webhook para um canal), selecione o canal e conclua.
3. Copie a **URL do webhook** gerada.
4. No `.env`: `NOTIFICAR_TEAMS_URL=` essa URL. Reinicie o sistema.
5. No painel do técnico: **Avisos para a equipe de TI** > **Enviar aviso de teste**.

O sistema envia um cartão e também um campo `text`, então funciona com o modelo que recebe cartão e com um fluxo criado
em branco (que usa `triggerBody()?['text']`). Se o Teams devolver erro 401, abra o fluxo e ajuste **Quem pode acionar o
fluxo** para **Qualquer pessoa**.

### E-mail (SMTP)

```
NOTIFICAR_EMAIL_PARA=ti@suaempresa.com.br,chefe-ti@suaempresa.com.br
SMTP_HOST=smtp.suaempresa.com.br
SMTP_PORT=587
SMTP_USER=avisos@suaempresa.com.br
SMTP_PASSWORD=...
SMTP_FROM=avisos@suaempresa.com.br
SMTP_SEGURANCA=starttls        # starttls (porta 587), ssl (porta 465) ou nenhuma
```

- Servidor SMTP interno sem senha: deixe `SMTP_USER` e `SMTP_PASSWORD` vazios, use a porta que ele aceita e `SMTP_SEGURANCA=nenhuma`.
- Muitos provedores de e-mail exigem liberar o envio por SMTP ou criar uma **senha de aplicativo**: peça ao responsável pelo e-mail.

### Webhook de texto (Slack, Google Chat, Mattermost...)

`NOTIFICAR_WEBHOOK_URL=` URL do webhook. O sistema envia `{"text": "..."}`.

Em todos os casos, preencha `URL_DO_SISTEMA` para o aviso trazer o link de acesso.

## 7. Backup e atualização

- **Backup:** painel do técnico > Manutenção > Preparar backup (baixa uma cópia completa), ou copie o arquivo do banco
  (`data/techassist.db`; no Docker, a pasta `dados/`). Guarde fora do servidor.
- **Atualizar:** siga a nota da versão em `versoes/` (arquivos novos, o que substituir e como testar). Guarde o zip da
  versão anterior para poder voltar.

## 8. Problemas comuns

| Sintoma | O que verificar |
|---|---|
| Outro computador não abre o endereço | Firewall (porta 8501), IP/nome correto, servidor ligado e sistema em modo servidor |
| Aviso de teste com erro | Mensagem exibida no painel; confira URL do Teams, host/porta/senha do SMTP e acesso à internet do servidor |
| Horários errados nos chamados | Fuso do servidor (Windows/Linux) ou `TZ` no Docker |
| Sistema não inicia com o Windows | Rode `servidor\IniciarServidor.bat` manualmente e leia o erro; confira se `.venv` e `.env` existem |
