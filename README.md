# TechAssist AI — protótipo inicial

Aplicação local de suporte técnico e gerenciamento básico de chamados.

## Requisitos
- Python 3.10 ou superior
- Conexão com a internet para consultar a API de IA
- Chave da API Groq (opcional para testar cadastro e gestão de chamados)

## Primeira execução em qualquer computador (recomendado)

1. Instale o Python 3.10 ou superior (https://www.python.org/downloads/) e marque **Add python.exe to PATH**.
2. Copie a pasta do projeto **sem** a pasta `.venv` (ela é específica de cada computador) e **sem** o arquivo `.env`.
3. Dê dois cliques em `IniciarTechAssist.bat` (Windows) ou execute `./IniciarTechAssist.sh` (Linux/macOS).
   Na primeira vez ele cria o ambiente, instala as bibliotecas (precisa de internet) e abre o `.env` para você
   preencher `TECHNICIAN_PASSWORD` e, se quiser usar a IA, `GROQ_API_KEY`.

Para levar os chamados já cadastrados, copie também `data/techassist.db`.

Atenção: cada computador que executa o sistema tem o **seu próprio banco de dados**. Para que todos os
funcionários registrem chamados no mesmo lugar, execute o sistema em **um único computador** e acesse pelo navegador.

## Instalação manual no Windows (PowerShell)

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
- Cadastro de chamados com código aleatório de 8 letras e números (ex.: K7M2X9QA)
- Tela de entrada: Funcionário (informa nome e setor) ou Técnico de TI (senha do `.env`)
- Consulta de chamados pelo nome do funcionário; o setor fica registrado em cada chamado
- Painel do técnico
- Atualização de status e histórico de anotações
- Persistência local em SQLite

## Limitações importantes do protótipo
- O acesso é uma tela simples: o funcionário informa nome e setor (sem senha) e a equipe técnica usa uma
  única senha definida no `.env`. Não é autenticação individual.
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
   - **Não resolveu**: o sistema abre um chamado automaticamente, com o nome e o setor informados ao entrar (categoria da solução, prioridade Média,
     com o relato do funcionário e os passos já tentados), informa o protocolo, encerra o assunto e pergunta
     se há mais algum problema.
   - Se o funcionário, em vez de clicar, escrever outra mensagem, a IA assume sabendo o que já foi tentado.
   - Conversa com a IA: depois de 5 mensagens do funcionário (ou 10 minutos de conversa, o que vier primeiro),
     o assistente pergunta se o problema foi resolvido, com os botões **Resolveu** e **Não resolveu**.
     Em **Não resolveu**, o chamado é aberto com o resumo das mensagens. Os limites ficam no começo do `app.py`
     (`MENSAGENS_ATE_PERGUNTAR` e `MINUTOS_ATE_PERGUNTAR`; use 0 nos minutos para desativar o tempo).
   - Mensagens curtas de encerramento são reconhecidas sem usar a IA: "terminar conversa", "tchau", "obrigado" e
     "não, só isso" encerram sem perguntar de novo; "resolveu" ou "funcionou" contam como resolvido; "não resolveu"
     (com uma solução pendente) funciona como o botão **Não resolveu**. Perguntas, mensagens longas ou com
     negação seguem o fluxo normal.
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


## Pesquisa na internet

Quando a base de soluções não resolve e a conversa vai para a IA, ela pode pesquisar na internet sozinha
(ferramenta de busca da Groq) para encontrar a solução de um erro específico, de um programa ou de um equipamento.

- A IA decide quando pesquisar; em conversas simples ela responde direto.
- Quando pesquisa, a resposta informa isso e mostra as páginas consultadas.
- A pesquisa usa apenas termos técnicos gerais; o prompt proíbe incluir nomes, setores, e-mails, IPs ou nomes
  de máquinas na busca. Mesmo assim, o texto da busca sai da empresa.
- O conteúdo encontrado na internet é só referência: a IA continua sem orientar comandos, registro do Windows,
  instalação de programas ou desativação de antivírus. Nesses casos ela encaminha para a TI.
- Funciona nos modelos `openai/gpt-oss-120b` (padrão), `openai/gpt-oss-20b` e `openai/gpt-oss-safeguard-20b`.
  Com outro modelo, a IA responde sem pesquisar.
- Se a pesquisa falhar, a IA responde normalmente sem ela (o motivo aparece na janela do programa).
- Para desligar, coloque `PESQUISA_WEB=off` no arquivo `.env` e reinicie.
- O painel do técnico mostra quantas pesquisas foram feitas.
