# TechAssist AI 1.1.1 — nota da versão

Data: 2026-11-25 · Tipo: PATCH (ajuste de organização e ferramenta de diagnóstico, sem funcionalidade nova)

## Por que esta versão
A 1.1.0 trouxe muitos arquivos de servidor misturados com os do sistema, e o sistema não abriu. Como o servidor fica para depois,
esta versão separa tudo o que é de servidor e acrescenta uma ferramenta que mostra, em português, o que está errado.

## O que mudou
1. **Diagnostico.bat**: dois cliques e ele confere Python, arquivos, bibliotecas, `.env`, banco e porta. Salva `diagnostico.txt`.
2. **Pasta `servidor/`** (para depois): Docker, serviço do Windows/Linux, exemplos de HTTPS e o guia de implantação.
3. **`IniciarTechAssist.bat`** simples de novo, só para uso local.
4. Versão **1.1.1** na tela.

As novidades da 1.1.0 continuam: avisos para a TI (e-mail, Teams, webhook), versão na tela, `CHANGELOG.md` e notas por versão.

## Arquivos
**Novos:** `Diagnostico.bat`, `diagnostico.py`, `servidor/LEIA-ME.md`, `versoes/NOTA_v1.1.1.md`.
**Alterados:** `versao.py`, `IniciarTechAssist.bat`, `IniciarTechAssist.sh`, `CHANGELOG.md`, `README.md`, `.gitignore`.
**Movidos para `servidor/`:** `Dockerfile`, `docker-compose.yml`, `IniciarServidor.bat`, `InstalarServicoWindows.bat`,
`RemoverServicoWindows.bat`, `techassist.service`, `Caddyfile.exemplo`, `nginx.conf.exemplo` e `IMPLANTACAO_SERVIDOR.md`.
**Sem alteração:** `app.py`, `database.py`, `knowledge.py`, `notificacoes.py`, `base_conhecimento.json`, `requirements.txt`, `tests/`.

## Como atualizar (leia com atenção)
1. Feche o sistema (feche a janela preta).
2. Extraia o `TechAssistAI_v1.1.1.zip` em uma pasta qualquer (por exemplo, a Área de Trabalho). Vai aparecer uma pasta `TechAssistAI`.
3. **Abra essa pasta, selecione TODO o conteúdo (Ctrl+A) e copie para dentro da pasta onde o sistema já está**, aceitando substituir.
   Não copie a pasta inteira por cima (isso cria uma pasta dentro da outra, e o sistema pode "não abrir" por estar na pasta errada).
4. Pode apagar da sua pasta, se existirem, os arquivos soltos da 1.1.0 que agora ficam em `servidor/`: `Dockerfile`, `docker-compose.yml`,
   `.dockerignore`, `IniciarServidor.bat`, `InstalarServicoWindows.bat`, `RemoverServicoWindows.bat` e as pastas `deploy` e `docs`.
   Se você chegou a rodar `InstalarServicoWindows.bat`, rode `servidor\RemoverServicoWindows.bat` como administrador.
5. Dê dois cliques em **`Diagnostico.bat`** e leia o resultado. Corrija o que aparecer como [ERRO].
6. Inicie pelo `IniciarTechAssist.bat`. A versão **1.1.1** aparece na tela de entrada.

Seu `.env`, `.venv` e o banco (`data/techassist.db`) não estão no zip e não são alterados.

## Se ainda não abrir
Envie o arquivo `diagnostico.txt` e as últimas linhas que aparecem na janela preta do `IniciarTechAssist.bat`.

## Banco de dados
Sem mudança de estrutura.

## Como testar
- Automáticos: `python -m unittest discover -s tests -v` (esperado: 35 testes, OK).
- Manual: `Diagnostico.bat` sem [ERRO]; sistema abre; entrar como funcionário e como técnico; abrir um chamado.

## Como voltar para a versão anterior
Extraia por cima o zip da versão anterior. O banco não mudou.
