# TechAssist AI 1.1.0 — nota da versão

Data: 2026-11-25 · Tipo: MINOR (funcionalidades novas, compatível com a 1.0.0)

## Resumo
1. **Avisos para a TI** por e-mail, Microsoft Teams e webhook de texto (chamado novo e resposta do funcionário).
2. **Servidor único:** modo servidor, início automático no Windows, serviço no Linux e Docker, com guia de implantação.
3. **Versionamento:** versão na tela, `CHANGELOG.md` e uma nota por versão.

## Arquivos
**Novos:** `notificacoes.py`, `versao.py`, `CHANGELOG.md`, `Dockerfile`, `docker-compose.yml`, `.dockerignore`,
`IniciarServidor.bat`, `InstalarServicoWindows.bat`, `RemoverServicoWindows.bat`, `deploy/` (3 arquivos),
`docs/IMPLANTACAO_SERVIDOR.md`, `versoes/NOTA_v1.1.0.md`, `tests/test_notificacoes.py`.

**Alterados:** `app.py`, `database.py`, `IniciarTechAssist.bat`, `IniciarTechAssist.sh`, `.env.example`, `README.md`.

**Sem alteração:** `knowledge.py`, `base_conhecimento.json`, `requirements.txt`, `tests/test_knowledge.py`,
`tests/test_database.py`. Seu `.env`, `.venv` e `data/techassist.db` **não** devem ser substituídos.

## Como atualizar
1. Guarde o zip da versão atual (para poder voltar).
2. Feche o sistema.
3. Extraia o `TechAssistAI_v1.1.0.zip` por cima da pasta do projeto, aceitando substituir. O zip não contém `.env`, `.venv` nem o banco.
4. Opcional: copie para o seu `.env` as linhas novas de `.env.example` (avisos e `URL_DO_SISTEMA`). Sem elas, tudo continua funcionando, apenas sem avisos.
5. Inicie pelo `IniciarTechAssist.bat`. A versão **1.1.0** aparece na tela de entrada.

## Banco de dados
Sem mudança de estrutura: não há migração, e o banco da 1.0.0 funciona na 1.1.0 e vice-versa.

## Como testar
- Automáticos: `python -m unittest discover -s tests -v` (esperado: 35 testes, OK).
- Manuais: abra um chamado e confira o aviso no canal configurado; no painel do técnico, **Avisos para a equipe de TI** >
  **Enviar aviso de teste**; abra a tela de entrada e confira a versão; em servidor, acesse de outro computador pelo IP.

## Como voltar para a versão anterior
Feche o sistema e extraia por cima o zip da 1.0.0. Os chamados continuam, pois o banco não mudou.

## Não verificado nesta entrega
Os avisos (SMTP, Teams), o Docker, o serviço do Windows e o systemd foram feitos com base na documentação, mas **não foram
executados em ambiente real**; os envios foram simulados em testes automatizados. Faça o teste de aviso e o teste de acesso
pela rede antes de liberar para os funcionários.
