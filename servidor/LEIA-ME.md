# Pasta servidor — PARA DEPOIS

Tudo aqui serve **somente** para quando o TechAssist AI for colocado em um servidor (um único computador que todos acessam
pelo navegador). **Para usar o sistema no seu computador, você não precisa de nada desta pasta.**

| Arquivo | Para que serve |
|---|---|
| `IMPLANTACAO_SERVIDOR.md` | Passo a passo completo (Windows, Linux, Docker, HTTPS, avisos) |
| `IniciarServidor.bat` / `iniciar_servidor.sh` | Iniciam o sistema acessível pela rede |
| `InstalarServicoWindows.bat` / `RemoverServicoWindows.bat` | Iniciar com o Windows (e remover) |
| `Dockerfile`, `docker-compose.yml`, `Dockerfile.dockerignore` | Rodar em Docker |
| `techassist.service` | Serviço do Linux (systemd) |
| `Caddyfile.exemplo`, `nginx.conf.exemplo` | Exemplos de HTTPS |

Antes de usar qualquer coisa daqui, o sistema precisa estar funcionando no computador (`IniciarTechAssist.bat`).
