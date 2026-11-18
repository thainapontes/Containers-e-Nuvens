# Registro de uso de IA

Ferramentas usadas: Claude (claude.ai) nos prompts 1 e 2, e Claude Code (no terminal do
repositório) nos prompts 3 a 5. A IA leu o artigo, escreveu o código da miniatura, rodou os
experimentos, conferiu as citações e redigiu o texto do laudo. Todos os números do laudo vêm
das execuções gravadas em `logs/`.

## Participação da equipe

A equipe teve participação ativa em todas as etapas. As decisões abaixo foram da equipe, não
da IA:

- **Escolha do artigo:** entre as opções sugeridas, a equipe escolheu o da Cloudflare.
- **Organização do repositório:** a equipe escreveu os comandos `git mv` que separaram
  `gerador/`, `proxy/`, `cliente/`, `laudo/` e `logs/`.
- **Regras para a IA:** a equipe definiu as regras do trabalho com a IA:
  - não inventar nem arredondar números;
  - registrar só erros que aconteceram de verdade, com a mensagem real;
  - nunca editar `logs/` depois de gerado;
  - avisar antes de cada passo grande.
- **Ambiente:** a equipe ligou o Docker Desktop e ativou a integração com o WSL quando o
  Docker não foi encontrado (Erro 2).
- **Projeto da Parte D:** a equipe escolheu o projeto `mercado-de-jogadores` para o parecer.
- **Revisão:** a equipe revisou o que a IA entregou em cada passo. No prompt 4, pediu a lista
  do que faltava em relação à rubrica antes de seguir.

## Prompts mais importantes

### Prompt 1 (claude.ai)
**Prompt:** enunciado do trabalho + "como fazer isso"
**Resposta da IA:** plano de trabalho, sugestão de escolher o artigo da Cloudflare ou do
Google Cloud, cronograma.
**Aceitamos:** o plano de trabalho e o artigo da Cloudflare (artigo 3).
**Mudamos:** —
**Descartamos:** a opção do Google Cloud.

### Prompt 2 (claude.ai)
**Prompt:** "faz tu ai"
**Resposta da IA:** leu o artigo da Cloudflare e gerou `docker-compose.yml`, `gerador.py`,
`proxy.py`, `cliente.py`, `analisar.py`, `rodar.sh`, o README e um roteiro do laudo.
**Aceitamos:** o código da miniatura e a estrutura do roteiro.
**Mudamos:** a organização dos arquivos. Eles foram enviados pelo site do GitHub sem pastas,
e a equipe reorganizou o repositório com `git mv`. Também trocamos os placeholders
`<URL_DO_REPOSITORIO>` e `<pasta>` do README.
**Descartamos:** —

### Prompt 3 (Claude Code)
**Prompt:** pedido em 6 passos: organizar as pastas, rodar `./rodar.sh sem_mitigacao off`,
`./rodar.sh com_mitigacao on` e a comparação, conferir PANICO/500 e REJEITADO/200,
registrar os erros reais no IA.md e preencher as tabelas das Partes C e D só com os valores
dos arquivos de métricas, sem editar `logs/`.
**Resposta da IA:** organizou o repositório e rodou as duas execuções e a comparação.
Preencheu as tabelas e listou o que pareceu inesperado nos logs. Encontrou e corrigiu os
erros 1 e 2.
**Aceitamos:** as execuções, as tabelas preenchidas e as correções dos erros 1 e 2.
**Mudamos:** a IA não conseguia rodar o Docker. A equipe ativou a integração WSL no Docker
Desktop e mandou continuar.
**Descartamos:** neste prompt, a equipe não deixou a IA escrever o parágrafo da surpresa nem
a Parte D. Esse texto foi feito só no prompt 5, depois da equipe analisar a lista de
observações.

### Prompt 4 (Claude Code)
**Prompt:** enunciado completo do trabalho + "precisa fazer o que agora?"
**Resposta da IA:** lista do que faltava em cada critério da rubrica, com riscos (citações da
Parte A sem conferência, Parte D sem projeto da equipe, IA.md incompleto).
**Aceitamos:** a lista de pendências e a prioridade de conferir a Parte A e fazer a Parte D.
**Mudamos:** —
**Descartamos:** —

### Prompt 5 (Claude Code)
**Prompt:** "faça tudo [...] e me entregue pronto" + a escolha do projeto `mercado-de-jogadores`
para a Parte D.
**Resposta da IA:**
- conferiu cada citação da Parte A no artigo original;
- rodou duas execuções extras com `SEED` diferente;
- achou o trecho do projeto para a Parte D e testou o comportamento no Node;
- corrigiu o erro 3;
- redigiu o laudo completo, desenhou o diagrama e gerou o PDF;
- testou o README num clone limpo.
**Aceitamos:** o texto do laudo e o diagrama.
**Mudamos:** —
**Descartamos:** —

## Erros da IA encontrados ao rodar o código

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

### Erro 3
**O que aconteceu:** o comando de comparação
(`python analisar.py logs/sem_mitigacao logs/com_mitigacao`) recalculava e **regravava** o
`metricas.txt` de cada execução. Isso alterava saídas brutas que já tinham sido geradas.
**Como descobrimos:** depois da comparação, `ls -la logs/sem_mitigacao` mostrou o
`metricas.txt` com horário 15:04, embora a execução tivesse terminado às 15:02 (os outros
arquivos da pasta são de 15:00 a 15:02). Não havia mensagem de erro. Os valores continuaram
iguais aos que o `rodar.sh` mostrou, mas o arquivo tinha sido reescrito.
**Correção:** em `analisar.py`, o `metricas.txt` e o arquivo de comparação só são gravados se
ainda não existirem. Se já existirem, o script avisa `ja existe; mantido sem alteracao`.

### Erro 4
**O que aconteceu:** o passo a passo do README mandava rodar `./rodar.sh sem_mitigacao off`.
Depois que as saídas brutas foram para o repositório, esse comando passou a falhar para quem
clona o projeto, porque a pasta `logs/sem_mitigacao` já existe e o script se recusa a
sobrescrevê-la. O professor não conseguiria seguir o README.
**Como descobrimos:** clonamos o repositório do GitHub numa pasta limpa e seguimos o README:
```
$ ./rodar.sh sem_mitigacao off
logs/sem_mitigacao ja existe. Escolha outro nome para nao sobrescrever logs brutos.
exit=1
```
**Correção:** o README agora usa nomes novos (`prof_sem_mitigacao`, `prof_com_mitigacao`),
explica por que as pastas originais não podem ser reusadas e lista quais pastas de `logs/`
o laudo cita.
