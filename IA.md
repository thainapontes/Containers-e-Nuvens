# Registro de uso de IA

Ferramenta usada: Claude (claude.ai). A IA foi usada para ler o artigo, escrever o código
da miniatura e montar a estrutura do laudo. Todos os números do laudo vêm das execuções
da equipe, em `logs/`.

## Prompts mais importantes

> A equipe deve completar as colunas "O que aceitamos / mudamos / descartamos" com o que
> realmente fez. Adicionem os prompts que usarem depois deste (máximo de 5 no total).

### Prompt 1
**Prompt:** enunciado do trabalho + "como fazer isso"
**Resposta da IA:** plano de trabalho, sugestão de escolher o artigo da Cloudflare ou do
Google Cloud, cronograma.
**Aceitamos:** _(preencher)_
**Mudamos:** _(preencher)_
**Descartamos:** _(preencher)_

### Prompt 2
**Prompt:** "faz tu ai"
**Resposta da IA:** leu o artigo da Cloudflare e gerou `docker-compose.yml`, `gerador.py`,
`proxy.py`, `cliente.py`, `analisar.py`, `rodar.sh`, o README e um roteiro do laudo.
**Aceitamos:** _(preencher)_
**Mudamos:** _(preencher: ex. parâmetros, nomes, trechos do roteiro reescritos)_
**Descartamos:** _(preencher)_

### Prompt 3
_(preencher)_

## Erros da IA encontrados ao rodar o código

> Registrem aqui pelo menos 2 erros que **vocês** encontraram ao rodar na máquina de vocês
> (mensagem de erro, comportamento estranho, número que não batia) e como corrigiram.
> Coisas para observar: permissões da pasta `logs/` no Linux, o script no Windows,
> tempos que não batem com a linha do tempo, métricas que não fazem sentido.

### Erro 1
**O que aconteceu:** ao dar permissão de execução com `git update-index --chmod=+x rodar.sh`,
o Git também gravou no commit o conteúdo do arquivo como estava no disco do Windows, com
quebras de linha CRLF. Um script bash com CRLF falha no Linux (`$'\r': command not found`).
Os outros arquivos também apareciam como modificados só por causa do CRLF.
**Como descobrimos:** `git show --stat HEAD` mostrou `rodar.sh | 32 +++++++++---------`
(16 linhas trocadas sem mudança de conteúdo), quando era para mudar só a permissão.
`git diff --ignore-cr-at-eol --stat` saiu vazio, confirmando que a diferença era só o CRLF.
O erro foi pego antes de rodar o script.
**Correção:** restauramos a versão LF (`git show HEAD~1:rodar.sh > rodar.sh`), aplicamos de
novo `git add` + `git update-index --chmod=+x` e corrigimos o commit com `git commit --amend`.
Nos demais arquivos convertemos CRLF para LF com `sed -i 's/\r$//'`.

### Erro 2
**O que aconteceu:** o Docker não estava acessível no terminal Linux (WSL 2), então
`./rodar.sh` não podia rodar. O Docker Desktop estava instalado no Windows, mas desligado e
sem a integração com o WSL ativada.
**Como descobrimos:** `docker --version` no WSL respondeu
`The command 'docker' could not be found in this WSL 2 distro. We recommend to activate the WSL integration in Docker Desktop settings.`
Ao tentar o `docker.exe` do Windows, apareceu
`failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine; check if the path is correct and if the daemon is running`.
Usar o `docker.exe` do Windows não resolveria, porque o `rodar.sh` monta `$PWD` (`/mnt/c/...`) como volume.
**Correção:** abrimos o Docker Desktop e ativamos a distro em Settings → Resources → WSL
Integration. Depois disso `docker --version` (29.7.2) e `docker compose version` (v5.5.1)
funcionaram no WSL e as duas execuções rodaram.
