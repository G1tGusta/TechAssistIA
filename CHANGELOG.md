# Histórico de versões do TechAssist AI

Formato: MAJOR.MINOR.PATCH. **MAJOR** = mudança que exige ajuste manual; **MINOR** = funcionalidade nova compatível;
**PATCH** = correção ou ajuste pequeno. A versão em uso aparece na tela de entrada e na barra lateral (arquivo `versao.py`).
A cada entrega há uma nota completa em `versoes/NOTA_vX.Y.Z.md`; guarde também o zip de cada versão.

## [1.1.2] — 2026-11-25

### Corrigido
- `IniciarTechAssist.bat` e `.sh` evitam a pergunta **"Email:"** que o Streamlit faz na primeira execução em um usuário novo
  (ela parece travar a abertura do sistema). Também passam a criar o `.env` mesmo que o `.env.example` não esteja na pasta.
- `.env.example` ausente deixou de ser tratado como erro no diagnóstico (só importa se o `.env` também não existir).

### Adicionado
- O diagnóstico agora **importa as bibliotecas de verdade** e **carrega a tela de entrada** como o navegador faria, mostrando o
  erro exato se houver. Usa um banco temporário: não cria nem altera o seu banco.
- `.streamlit/config.toml` (desliga a coleta de estatísticas do Streamlit).

### Banco de dados
- Sem mudança de estrutura.

## [1.1.1] — 2026-11-25

### Adicionado
- **Diagnostico.bat** (e `diagnostico.py`): confere Python, arquivos, versões dos módulos, bibliotecas, `.env`, base de
  soluções, banco e porta, e explica em português o que corrigir. Salva `diagnostico.txt`.

### Alterado
- Tudo o que é de servidor (Docker, serviço do Windows/Linux, HTTPS e o guia) foi movido para a pasta `servidor/`, marcada
  como **para depois**. O uso no seu computador não depende dela.
- `IniciarTechAssist.bat` e `.sh` voltaram à versão simples de uso local (sem modo servidor).

### Banco de dados
- Sem mudança de estrutura.

## [1.1.0] — 2026-11-25

### Adicionado
- **Avisos para a equipe de TI** quando nasce um chamado e quando o funcionário responde: e-mail (SMTP), Microsoft Teams
  (fluxo de trabalho/Workflows) e webhook de texto. Envio em segundo plano, com botão de teste no painel do técnico.
- **Execução em servidor único:** modo servidor nos scripts (`IniciarServidor.bat`, `IniciarTechAssist.sh servidor`),
  início automático no Windows (`InstalarServicoWindows.bat`), serviço systemd (`deploy/techassist.service`),
  `Dockerfile` e `docker-compose.yml`, exemplos de HTTPS (Caddy e Nginx).
- Variável `TECHASSIST_DB` para definir o caminho do banco.
- Versão exibida na tela de entrada e na barra lateral; este histórico e as notas por versão.
- Guia `docs/IMPLANTACAO_SERVIDOR.md`.
- 10 testes automatizados novos (avisos), totalizando 35.

### Alterado
- `IniciarTechAssist.bat` e `.sh` aceitam o argumento `servidor`.
- `.env.example` com as variáveis dos avisos.

### Banco de dados
- Sem mudança de estrutura.

## [1.0.0] — 2026-11-25 (base consolidada, etapas 1 a 10)

Tudo o que existia até a entrega anterior, agora numerado:
- Chat com IA (Groq) e pesquisa na internet; base de soluções da TI (12 soluções) antes da IA.
- Perguntas "resolveu?" (após a base e após a conversa com a IA, por 5 mensagens ou 10 minutos); reconhecimento de encerramento.
- Chamado automático e manual, com código aleatório de 8 caracteres, nome e setor; tela de entrada (Funcionário e Técnico de TI).
- Conversa dentro do chamado, anotações internas; painel do técnico com filtros, CSV, taxa de autoatendimento,
  assuntos sem solução e backup; atalhos de problemas comuns.
- Scripts de inicialização (Windows e Linux/macOS), testes automatizados (25) e documentação.
