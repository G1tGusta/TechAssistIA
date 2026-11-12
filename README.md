# TechAssist AI — protótipo inicial

Aplicação local de suporte técnico e gerenciamento básico de chamados.

## Requisitos
- Python 3.10 ou superior
- Conexão com a internet para consultar a API de IA
- Chave da API Groq (opcional para testar cadastro e gestão de chamados)

## Instalação no Windows (PowerShell)

```powershell
cd TechAssist_AI
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edite o arquivo `.env` e informe sua chave `GROQ_API_KEY`.

## Executar

```powershell
streamlit run app.py
```

O navegador abrirá a aplicação localmente. Se não abrir, acesse:
http://localhost:8501

## O que já funciona
- Base de soluções da TI: antes de chamar a IA, o assistente verifica se o problema já é conhecido e envia o passo a passo pronto (sem custo de API)
- Chat com IA via Groq, quando a chave estiver configurada
- Cadastro de chamados com código aleatório de 8 letras e números (ex.: K7M2X9QA); o nome de quem abre o chamado é perguntado antes do envio
- Consulta de chamados pelo identificador do solicitante
- Painel do técnico
- Atualização de status e histórico de anotações
- Persistência local em SQLite

## Limitações importantes do protótipo
- A seleção Funcionário/Técnico é apenas uma simulação, não é autenticação.
- Não exponha a aplicação na rede da empresa antes de implementar login,
  autorização por perfil, backups e controles de segurança.
- Não insira senhas, dados pessoais sensíveis, endereços internos ou informações
  confidenciais nos testes.
- O modelo de IA pode errar. Valide procedimentos antes de aplicá-los.
- A IA ainda não cria chamados automaticamente a partir da conversa; isso será
  desenvolvido na próxima etapa.

## Próximas evoluções
1. Classificação automática de categoria e prioridade.
2. Criar chamado diretamente a partir da conversa.
3. Busca na base de conhecimento.
4. Autenticação e perfis reais.
5. Relatórios e indicadores.


## Separação entre funcionário e técnico

- Funcionários podem abrir solicitações e consultar somente os chamados associados à identificação informada.
- A área de Técnico de TI exige a variável `TECHNICIAN_PASSWORD` no arquivo `.env`.
- Funcionários não escolhem prioridade; os chamados entram como `Média` e a equipe de TI pode ajustar a prioridade no painel técnico.
- Configure uma senha forte e não compartilhe o arquivo `.env`.

**Importante:** esta senha simples é adequada apenas para protótipo local. Antes de disponibilizar o sistema na rede da empresa, implemente autenticação individual, controle de sessão e autorização no servidor; não use apenas a seleção de área como segurança.


## Base de soluções da TI (executada antes da API)

Fluxo do assistente:

1. O funcionário descreve o problema no chat.
2. O sistema procura na `base_conhecimento.json` uma solução que combine com as palavras da mensagem.
3. Se encontrar, envia o passo a passo e pergunta **"Resolveu?"**:
   - **Resolveu**: a conversa termina sem chamado e sem usar a API.
   - **Não resolveu**: o sistema pergunta o nome do funcionário e abre um chamado automaticamente (categoria da solução, prioridade Média,
     com o relato do funcionário e os passos já tentados), informa o protocolo, encerra o assunto e pergunta
     se há mais algum problema.
   - Se o funcionário, em vez de clicar, escrever outra mensagem, a IA assume sabendo o que já foi tentado.
4. Se não encontrar nenhuma solução conhecida, a conversa vai direto para a IA.

O painel do técnico mostra quantas soluções foram sugeridas, quantas resolveram sem chamado e quantas não resolveram.

### Como adicionar ou ajustar uma solução

Abra `base_conhecimento.json` e copie uma entrada existente. Campos:

- `id`: nome curto e único, sem espaços (ex.: `vpn-nao-conecta`).
- `titulo`: título mostrado ao funcionário.
- `palavras_chave`: palavras ou expressões que o funcionário costuma usar. Maiúsculas, acentos e plural são
  ignorados. Expressões com mais de uma palavra valem mais pontos que palavras soltas.
- `passos`: lista de passos simples, na ordem. Escreva para quem não é da TI e evite comandos ou configurações avançadas.
- `resultado_esperado` (opcional): o que deve acontecer se der certo.
- `categoria_chamado`: categoria usada no chamado automático (use um nome da lista do formulário, ex.: `Rede / Internet`; se faltar, usa `Outro`).
- `quando_abrir_chamado` (opcional): critério mostrado à IA quando o funcionário escreve em vez de clicar nos botões.

O arquivo é relido automaticamente: não precisa reiniciar o sistema. Se houver erro de digitação no JSON,
o sistema continua usando a última versão válida.
