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
  Docker não foi encontrado (ver "Problema de ambiente").
- **Projeto da Parte D:** a equipe corrigiu a IA, que tinha usado o projeto `mercado-de-jogadores`,
  e indicou o projeto da disciplina, o `Marketplace-da-economia-criativa`.
- **Equipe e artigo:** a equipe conferiu no mural da turma que o artigo 3 tinha só uma outra equipe
  (o limite é duas) e informou os nomes para o cabeçalho do laudo.
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
Preencheu as tabelas e listou o que pareceu inesperado nos logs. Encontrou e corrigiu o erro 1.
**Aceitamos:** as execuções, as tabelas preenchidas e a correção do erro 1.
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
**Prompt:** "faça tudo [...] e me entregue pronto"; depois, "ele cumpre tudo que a atividade pediu?"
e a correção do projeto da Parte D.
**Resposta da IA:**
- conferiu cada citação da Parte A no artigo original;
- rodou duas execuções extras com `SEED` diferente;
- achou o trecho do projeto para a Parte D e testou o comportamento no Node;
- corrigiu o erro 2;
- redigiu o laudo completo, desenhou o diagrama e gerou o PDF;
- testou o README num clone limpo.
**Aceitamos:** o texto do laudo e o diagrama.
**Mudamos:**
- a IA escreveu na Parte D que as 11 rejeições mantiveram a versão 11. No
  `logs/com_mitigacao/proxy.log`, só as 9 últimas mantiveram a versão 11 (as duas primeiras mantiveram
  as versões 7 e 9). O texto foi corrigido.
- a IA tinha feito a Parte D sobre o `mercado-de-jogadores`, que não é o projeto da disciplina.
  Refizemos a Parte D sobre o `Marketplace-da-economia-criativa`, rodando o worker real do projeto
  contra um PostgreSQL temporário (`logs/parte_d/teste_lote_worker.txt`) e o `env.js` real
  (`logs/parte_d/teste_port_env.txt`).
**Descartamos:** o trecho `env.ts:26` do `mercado-de-jogadores` e o log `teste_port_node.txt`.

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
**O que aconteceu:** o comando de comparação
(`python analisar.py logs/sem_mitigacao logs/com_mitigacao`) recalculava e **regravava** o
`metricas.txt` de cada execução. Isso alterava saídas brutas que já tinham sido geradas.
**Como descobrimos:** depois da comparação, `ls -la logs/sem_mitigacao` mostrou o
`metricas.txt` com horário 15:04, embora a execução tivesse terminado às 15:02 (os outros
arquivos da pasta são de 15:00 a 15:02). Não havia mensagem de erro. Os valores continuaram
iguais aos que o `rodar.sh` mostrou, mas o arquivo tinha sido reescrito.
**Correção:** em `analisar.py`, o `metricas.txt` e o arquivo de comparação só são gravados se
ainda não existirem. Se já existirem, o script avisa `ja existe; mantido sem alteracao`.

### Erro 3
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

### Erro 4
**O que aconteceu:** no parágrafo da surpresa (Parte C), a IA usou como prova de que o
healthcheck não marcou o proxy como `unhealthy` a falta de linhas `unhealthy` no `compose.log`.
Essa prova não vale: o `docker compose up` só mostra a saúde dos containers na subida, quando o
`depends_on` espera por eles, e não registra mudanças depois disso.
**Como descobrimos:** numa revisão do repositório, rodamos a miniatura gravando o estado do
healthcheck do proxy a cada segundo com `docker inspect`. Depois repetimos com uma cópia
temporária do `proxy.py` em que o `/health` responde 500 durante o pânico: o `docker inspect`
passou a mostrar `unhealthy`, mas o `compose.log` continuou só com as duas linhas da subida
(`Container ...-gerador-1 Healthy` e `Container ...-proxy-1 Healthy`).
**Correção:** o `rodar.sh` agora grava `saude.log` (estado do healthcheck uma vez por segundo) e
o `analisar.py` conta as amostras entre o primeiro e o último erro. Refizemos as execuções
(`logs/*_v2`) e o laudo passou a citar `healthy=33 (de 33 amostras)` de
`logs/sem_mitigacao_v2/metricas.txt`. As execuções antigas continuam em `logs/` como histórico.

## Problema de ambiente (não foi erro da IA)

Registrado aqui porque bloqueou a execução, mas a causa era a configuração da máquina, não
o código gerado pela IA.

### Docker indisponível no WSL
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

## Revisão final do repositório

Antes da entrega, pedimos à IA uma revisão do repositório contra o enunciado e a rubrica, e
depois que validasse cada ponto e aplicasse as correções, um commit por ponto.
**Aceitamos:** `.gitattributes` com LF, remoção do rascunho `ROTEIRO_LAUDO.md`, links da Parte D
fixos no commit testado, separação do problema de ambiente, `trap` no `rodar.sh`, usuário dos
containers, leitura sob lock no `proxy.py` e o `saude.log` (Erro 4).
**Mudamos:** a sugestão de rodar os containers com `user: ${UID}:${GID}` virou
`${HOST_UID:-0}:${HOST_GID:-0}`, exportado pelo `rodar.sh`, porque o Bash não exporta `UID` e,
sem o script, o `docker compose up` direto passaria a falhar ao gravar em `logs/`.
**Descartamos:** juntar a função `log()` do gerador e do proxy num arquivo só, porque cada
container monta apenas a própria pasta.

