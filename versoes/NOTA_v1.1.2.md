# TechAssist AI 1.1.2 — nota da versão

Data: 2026-11-25 · Tipo: PATCH (correção de abertura e diagnóstico mais completo)

## Por que esta versão
O diagnóstico da 1.1.1 no seu computador mostrou o sistema quase todo correto (Python, bibliotecas, `.env`, senha do técnico,
chave da IA, módulos e porta OK). O único erro era a falta do `.env.example`, que não impede nada. Mesmo assim o sistema podia
"não abrir": na **primeira execução em um usuário novo do Windows**, o Streamlit pergunta `Email:` na janela preta e espera
você apertar Enter, o que parece travamento. Esta versão evita essa pergunta e torna o diagnóstico capaz de apontar o erro exato.

## O que mudou
1. `IniciarTechAssist.bat` (e `.sh`): evitam a pergunta "Email:" e criam o `.env` mesmo sem o `.env.example`.
2. `Diagnostico.bat`: importa as bibliotecas de verdade e carrega a tela de entrada do sistema, mostrando o erro exato. Usa banco temporário.
3. `.streamlit/config.toml`: sem coleta de estatísticas.
4. Versão **1.1.2** na tela.

## Arquivos
**Alterados:** `IniciarTechAssist.bat`, `IniciarTechAssist.sh`, `diagnostico.py`, `versao.py`, `CHANGELOG.md`, `README.md`.
**Novos:** `.streamlit/config.toml`, `versoes/NOTA_v1.1.2.md`.
**Sem alteração:** `app.py`, `database.py`, `knowledge.py`, `notificacoes.py`, `base_conhecimento.json`, `requirements.txt`, `tests/`, `servidor/`.

## Como atualizar
1. Feche o sistema.
2. Extraia o zip em uma pasta qualquer; abra a pasta `TechAssistAI` que aparece, selecione **todo o conteúdo** (Ctrl+A) e copie para
   dentro da pasta onde o sistema está, aceitando substituir. Copie também a pasta oculta-ou-não `.streamlit` e os arquivos que começam com ponto
   (`.env.example`, `.gitignore`).
3. Rode `Diagnostico.bat` e depois `IniciarTechAssist.bat`. A versão **1.1.2** aparece na tela de entrada.

## Se aparecer "Email:" na janela preta
É só apertar **Enter** (nesta versão a pergunta deixa de aparecer).

## Se ainda não abrir
Envie o `diagnostico.txt` (agora ele mostra o erro exato) e as últimas linhas da janela preta.

## Banco de dados
Sem mudança de estrutura. O diagnóstico não cria nem altera o seu banco.

## Como voltar para a versão anterior
Extraia por cima o zip da versão anterior.
