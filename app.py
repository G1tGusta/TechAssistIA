import os
import streamlit as st
from dotenv import load_dotenv
from database import init_db, create_ticket, list_tickets, update_ticket, get_messages, log_kb_event, kb_stats
from knowledge import find_solution, get_entry, format_solution, context_for_ai, ticket_description

load_dotenv()
init_db()

# Depois que o chamado automático é aberto, leva o funcionário para a aba "Meus chamados".
# Para continuar no chat após abrir o chamado, troque para False.
IR_PARA_MEUS_CHAMADOS_APOS_ABRIR = True

st.set_page_config(page_title="TechAssist AI", page_icon="🛠️", layout="wide")
st.title("🛠️ TechAssist AI")
st.caption("Autoatendimento de TI: orientações simples, passo a passo, antes de abrir um chamado")

# --- Provedor de IA ---
def ask_ai(messages):
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return ("O modo de IA ainda não está configurado. Adicione sua chave GROQ_API_KEY "
                "ao arquivo .env. Enquanto isso, você pode registrar e consultar chamados.")
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()
        # Migra automaticamente a configuração antiga, já descontinuada na Groq.
        if model == "llama-3.3-70b-versatile":
            model = "openai/gpt-oss-120b"

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=900,
        )
        return response.choices[0].message.content
    except Exception as exc:
        return f"Não foi possível consultar a IA: {exc}"

SYSTEM_PROMPT = """
Você é o TechAssist AI, um assistente de autoatendimento de TI para funcionários.
Seu principal objetivo é ensinar a pessoa a resolver problemas simples sozinha,
com orientações práticas, amigáveis e em linguagem comum, reduzindo chamados
que podem ser resolvidos com verificações básicas.

COMO CONVERSAR:
- Fale em português brasileiro, com tom paciente, acolhedor e sem jargões.
- Comporte-se como um tutorial para alguém que não trabalha com TI.
- Primeiro entenda o sintoma e faça no máximo uma pergunta simples por vez.
- Dê instruções curtas, numeradas e fáceis de seguir. Explique onde clicar ou o
  que observar; não comece com comandos, configurações avançadas ou siglas.
- Oriente uma ou duas verificações por vez e peça para a pessoa contar o resultado.
- Diga o que deve acontecer em cada etapa e como desfazer algo simples, quando
  aplicável.

PRIORIZE SOLUÇÕES SIMPLES E SEGURAS:
- Sem internet: confira se o cabo de rede está conectado nas duas pontas e se
  há luzes na entrada de rede; se usa Wi-Fi, confira se o Wi-Fi está ligado,
  modo avião desligado e se está conectada à rede correta. Depois, teste outro
  site e verifique se outros dispositivos também estão sem internet.
- Outros exemplos: conferir energia e cabos de monitor/impressora, papel e
  mensagens de erro da impressora, volume e dispositivo de áudio selecionado,
  fechar e reabrir um aplicativo, conferir se Caps Lock está ligado, verificar
  se o carregador está conectado e reiniciar o aplicativo antes do computador.
- Adapte os passos ao problema relatado; não despeje uma lista enorme de dicas.
- Se a orientação resolver, confirme com o usuário e diga que não é necessário
  abrir chamado naquele momento.

QUANDO ENCAMINHAR PARA A TI:
- Se as verificações simples não resolverem, o problema voltar frequentemente,
  afetar várias pessoas, envolver acesso/permissões, suspeita de falha de rede,
  servidor ou sistema corporativo, ou exigir acesso administrativo.
- Explique com clareza por que precisa da equipe de TI e ajude a pessoa a
  descrever o que já tentou ao abrir o chamado.
- Não pressione o usuário a abrir chamado quando o problema foi resolvido.

SEGURANÇA:
- Nunca peça senhas, tokens, chaves privadas ou códigos de autenticação.
- Não oriente o funcionário a abrir equipamentos, mexer em tomadas/fiação
  elétrica, desativar antivírus/firewall, alterar configurações administrativas,
  executar comandos ou modificar servidores e equipamentos de rede.
- Se houver cheiro de queimado, faísca, líquido ou risco elétrico, oriente a
  parar de usar o equipamento e procurar a equipe responsável.
- Você não executa ações no computador; apenas orienta.
- Se não souber, seja transparente e encaminhe para a equipe de TI.

Seu foco é resolver o básico com o funcionário, não impressioná-lo com termos
 técnicos. Seja objetivo, cordial e didático.
"""

def build_ai_history(chat_history, extra_context=None):
    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    if extra_context:
        history.append({"role": "system", "content": extra_context})
    return history + chat_history[-12:]

def clean_name(raw):
    """Remove espaços extras e limita o tamanho do nome."""
    return " ".join(str(raw).split())[:60]

def name_is_valid(name):
    return len(name) >= 2 and any(c.isalpha() for c in name)

def open_auto_ticket(entry, requester):
    """Abre o chamado automático (o passo a passo não resolveu) e encerra o assunto no chat."""
    report = st.session_state.kb_pending_text or entry["titulo"]
    log_kb_event(entry["id"], requester, "nao_resolveu")
    protocol = create_ticket(
        requester,
        entry["titulo"],
        entry.get("categoria_chamado", "Outro"),
        "Média",
        ticket_description(entry, report),
    )
    st.session_state.chat_history.append({
        "role": "user",
        "content": f"Fiz o passo a passo \"{entry['titulo']}\" e o problema continua.",
    })
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": f"Obrigado, {requester}! Abri o chamado **{protocol}** em seu nome, com o que você relatou e os "
                   "passos que já tentou, então a equipe de TI não vai precisar perguntar tudo de novo. "
                   "Guarde esse código para acompanhar o andamento na aba **Meus chamados**.\n\n"
                   "Este problema está encerrado por aqui. **Posso ajudar com mais algum problema?**",
    })
    # Encerra este assunto e libera a base para um novo problema.
    st.session_state.kb_pending = None
    st.session_state.kb_pending_text = ""
    st.session_state.kb_tried = []
    st.session_state.kb_awaiting_name = False
    if IR_PARA_MEUS_CHAMADOS_APOS_ABRIR:
        st.session_state["ir_para_aba"] = "Meus chamados"
        st.session_state["chamado_novo"] = protocol

# A seleção separa as áreas; a área técnica exige senha configurada no .env.
st.sidebar.header("Acesso ao sistema")
role = st.sidebar.radio("Selecione sua área", ["Funcionário", "Técnico de TI"], key="area_acesso")
if role == "Funcionário":
    registered_name = st.session_state.get("nome_funcionario", "")
    if registered_name:
        st.sidebar.write(f"👤 **{registered_name}**")
        if st.sidebar.button("Trocar nome"):
            st.session_state.pop("nome_funcionario", None)
            st.rerun()
    else:
        st.sidebar.caption("Seu nome será pedido na hora de abrir um chamado.")
    user = registered_name or "Não informado"
else:
    user = st.sidebar.text_input("Seu nome (técnico)", value="Técnico de TI")
st.sidebar.caption("Ambiente local de desenvolvimento.")

if role == "Funcionário":
    st.header("Área do funcionário")
    st.caption("Abra solicitações e acompanhe somente os chamados registrados em seu nome.")
    # Navegação por botões (em vez de st.tabs) para o sistema poder mudar de tela sozinho.
    if "ir_para_aba" in st.session_state:
        st.session_state["aba_funcionario"] = st.session_state.pop("ir_para_aba")
    aba = st.radio("Navegação", ["Assistente", "Abrir chamado", "Meus chamados"],
                   horizontal=True, key="aba_funcionario", label_visibility="collapsed")

    if aba == "Assistente":
        st.subheader("Vamos tentar resolver juntos")
        st.caption("Conte o que aconteceu. Vou orientar verificações simples, uma etapa de cada vez. Se precisar da equipe de TI, também vou ajudar você a preparar o chamado.")
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        if "kb_pending" not in st.session_state:
            st.session_state.kb_pending = None   # solução sugerida aguardando resposta
        if "kb_pending_text" not in st.session_state:
            st.session_state.kb_pending_text = ""  # relato original do problema
        if "kb_awaiting_name" not in st.session_state:
            st.session_state.kb_awaiting_name = False  # perguntando o nome para abrir o chamado
        if "kb_tried" not in st.session_state:
            st.session_state.kb_tried = []       # soluções já sugeridas nesta conversa

        # O histórico fica em uma área rolável; o campo de envio fica sempre
        # abaixo dele, em vez do componente st.chat_input fixado pelo Streamlit.
        with st.container(height=520, border=True):
            if not st.session_state.chat_history:
                st.info("Ainda não há mensagens. Escreva sua dúvida no campo abaixo para começar.")
            for item in st.session_state.chat_history:
                with st.chat_message(item["role"]):
                    st.markdown(item["content"])

        pending_entry = get_entry(st.session_state.kb_pending) if st.session_state.kb_pending else None
        if pending_entry and st.session_state.kb_awaiting_name:
            # Antes de enviar o chamado, pergunta (ou confirma) o nome de quem está abrindo.
            st.write("**Para abrir o chamado, qual é o seu nome?**")
            with st.form("kb_name_form"):
                typed_name = st.text_input(
                    "Seu nome",
                    value=st.session_state.get("nome_funcionario", ""),
                    placeholder="Ex.: Maria Silva",
                )
                f_send, f_back = st.columns(2)
                send = f_send.form_submit_button("📨 Abrir chamado", type="primary", use_container_width=True)
                back = f_back.form_submit_button("Voltar", use_container_width=True)
            if back:
                st.session_state.kb_awaiting_name = False
                st.rerun()
            if send:
                name = clean_name(typed_name)
                if not name_is_valid(name):
                    st.error("Digite o seu nome para eu registrar o chamado.")
                else:
                    st.session_state["nome_funcionario"] = name
                    open_auto_ticket(pending_entry, name)
                    st.rerun()
        elif pending_entry:
            st.write("**Esse passo a passo resolveu o seu problema?**")
            b_ok, b_no = st.columns(2)
            if b_ok.button("✅ Resolveu, obrigado!", use_container_width=True, key="kb_ok"):
                log_kb_event(pending_entry["id"], user, "resolveu")
                st.session_state.kb_pending = None
                st.session_state.kb_pending_text = ""
                st.session_state.kb_tried = []
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": "Que bom que resolveu! 🎉 Não é necessário abrir chamado. "
                               "Posso ajudar com mais algum problema?",
                })
                st.rerun()
            if b_no.button("❌ Não resolveu", use_container_width=True, key="kb_no"):
                st.session_state.kb_awaiting_name = True  # pede o nome antes de abrir o chamado
                st.rerun()

        with st.form("assistant_chat_form", clear_on_submit=True):
            prompt = st.text_input(
                "Sua mensagem",
                placeholder="Ex.: estou sem internet, a impressora não imprime...",
                label_visibility="collapsed",
            )
            submitted = st.form_submit_button("Enviar mensagem", type="primary", use_container_width=True)

        if submitted and prompt.strip():
            text = prompt.strip()
            st.session_state.chat_history.append({"role": "user", "content": text})

            # Se havia uma solução aguardando resposta e o funcionário escreveu em vez de
            # clicar nos botões, considera que ela não resolveu e informa isso à IA.
            previous = get_entry(st.session_state.kb_pending) if st.session_state.kb_pending else None
            if previous:
                log_kb_event(previous["id"], user, "nao_resolveu")
                st.session_state.kb_pending = None
                st.session_state.kb_awaiting_name = False

            # 1º) Base de soluções da TI (sem usar a API).
            entry = find_solution(text, ignore_ids=st.session_state.kb_tried)
            if entry:
                st.session_state.kb_tried.append(entry["id"])
                st.session_state.kb_pending = entry["id"]
                st.session_state.kb_pending_text = text
                log_kb_event(entry["id"], user, "sugerida")
                st.session_state.chat_history.append({"role": "assistant", "content": format_solution(entry)})
            else:
                # 2º) Nenhuma solução conhecida: usa a IA (com o que já foi tentado, se houver).
                extra = context_for_ai(previous) if previous else None
                answer = ask_ai(build_ai_history(st.session_state.chat_history, extra))
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
            # Recarrega a tela para a nova resposta aparecer no histórico,
            # acima do campo de digitação.
            st.rerun()

    elif aba == "Abrir chamado":
        st.subheader("Registrar solicitação")
        st.info("Antes de abrir um chamado, tente o passo a passo do Assistente. Se o problema continuar, registre aqui o que aconteceu e o que você já tentou. A prioridade será definida pela equipe de TI.")
        with st.form("ticket_form", clear_on_submit=True):
            requester_name = st.text_input("Seu nome", value=st.session_state.get("nome_funcionario", ""),
                                           placeholder="Ex.: Maria Silva")
            title = st.text_input("Assunto", placeholder="Ex.: Não consigo acessar o sistema")
            category = st.selectbox("Categoria", [
                "Computador / Windows", "Linux", "Rede / Internet", "Acesso / Sistemas",
                "Impressora / Periféricos", "Servidor / Active Directory",
                "Firewall / pfSense", "Telefonia / Issabel / MicroSIP", "Outro"
            ])
            description = st.text_area("Descreva o problema", height=140)
            submitted = st.form_submit_button("Criar chamado", type="primary")
            if submitted:
                name = clean_name(requester_name)
                if not name_is_valid(name):
                    st.error("Informe o seu nome para registrar o chamado.")
                elif not title.strip() or not description.strip():
                    st.error("Preencha o assunto e a descrição.")
                else:
                    st.session_state["nome_funcionario"] = name
                    # Prioridade inicial definida pelo sistema; somente a equipe de TI altera depois.
                    ticket_id = create_ticket(name, title.strip(), category, "Média", description)
                    st.success(f"Chamado criado: **{ticket_id}** em nome de {name}. "
                               "Guarde esse código para acompanhar o andamento em Meus chamados.")

    else:
        st.subheader("Meus chamados")
        novo = st.session_state.pop("chamado_novo", None)
        if novo:
            st.success(f"Chamado **{novo}** aberto automaticamente com o que você relatou e os passos que já tentou. "
                       "A equipe de TI vai dar continuidade.")
            if st.button("⬅️ Voltar ao assistente (tenho outro problema)"):
                st.session_state["ir_para_aba"] = "Assistente"
                st.rerun()
        my_name = st.session_state.get("nome_funcionario", "")
        if not my_name:
            st.info("Informe o seu nome para ver os chamados registrados em seu nome.")
            with st.form("nome_form"):
                typed = st.text_input("Seu nome", placeholder="Ex.: Maria Silva")
                ok = st.form_submit_button("Ver meus chamados", type="primary")
            if ok:
                name = clean_name(typed)
                if name_is_valid(name):
                    st.session_state["nome_funcionario"] = name
                    st.rerun()
                else:
                    st.error("Digite o seu nome.")
        else:
            st.caption(f"Chamados registrados em nome de **{my_name}**.")
            tickets = list_tickets(requester=my_name)
            if tickets:
                st.dataframe(tickets, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum chamado encontrado para este nome.")

else:
    st.header("Área restrita — Técnico de TI")
    configured_password = os.getenv("TECHNICIAN_PASSWORD", "").strip()
    if not configured_password:
        st.error("A senha da equipe técnica ainda não foi configurada. Defina TECHNICIAN_PASSWORD no arquivo .env e reinicie o sistema.")
        st.stop()

    entered_password = st.text_input("Senha de acesso técnico", type="password")
    if entered_password != configured_password:
        st.warning("Informe a senha técnica para acessar os chamados e as ferramentas administrativas.")
        st.stop()

    st.success("Acesso técnico autorizado.")
    st.caption("Nesta área, a equipe de TI pode visualizar todos os chamados e definir prioridade e status.")
    kb = kb_stats()
    st.subheader("Autoatendimento (base de soluções)")
    k1, k2, k3 = st.columns(3)
    k1.metric("Soluções sugeridas", kb.get("sugerida", 0))
    k2.metric("Resolvidas sem chamado", kb.get("resolveu", 0))
    k3.metric("Não resolveram", kb.get("nao_resolveu", 0))
    st.divider()
    all_tickets = list_tickets()
    if all_tickets:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total de chamados", len(all_tickets))
        c2.metric("Abertos", sum(1 for x in all_tickets if x["status"] == "Aberto"))
        c3.metric("Em atendimento", sum(1 for x in all_tickets if x["status"] == "Em atendimento"))
        st.dataframe(all_tickets, use_container_width=True, hide_index=True)
        st.divider()
        st.subheader("Administrar chamado")
        ids = [x["protocolo"] for x in all_tickets]
        selected = st.selectbox("Protocolo", ids)
        current = next(x for x in all_tickets if x["protocolo"] == selected)
        st.write(f"**{current['assunto']}** — {current['solicitante']}")
        st.write(current["descricao"])
        statuses = ["Aberto", "Em atendimento", "Aguardando usuário", "Resolvido", "Fechado"]
        new_status = st.selectbox("Status", statuses, index=statuses.index(current["status"]))
        priorities = ["Baixa", "Média", "Alta", "Crítica"]
        current_priority = current["prioridade"] if current["prioridade"] in priorities else "Média"
        new_priority = st.selectbox("Prioridade definida pela TI", priorities, index=priorities.index(current_priority))
        resolution = st.text_area("Anotação técnica / solução aplicada")
        if st.button("Salvar atualização", type="primary"):
            update_ticket(selected, new_status, resolution, user, new_priority)
            st.success("Chamado atualizado.")
            st.rerun()
        with st.expander("Histórico do chamado"):
            for msg in get_messages(selected):
                st.markdown(f"**{msg['autor']}** · {msg['criado_em']}")
                st.write(msg["mensagem"])
    else:
        st.info("Ainda não existem chamados cadastrados.")
