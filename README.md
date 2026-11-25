# Miniatura do incidente da Cloudflare (18/11/2025)

Reprodução em miniatura, com Docker Compose, do mecanismo central do incidente descrito em
<https://blog.cloudflare.com/18-november-2025-outage/>: um arquivo de configuração gerado
automaticamente dobra de tamanho, passa de um limite fixo pré-alocado no proxy, e o proxy
passa a responder 5xx. O rollout gradual da mudança no banco faz o sistema **oscilar** entre
arquivo bom e arquivo ruim antes de falhar de vez.

## Requisitos

- Docker com o plugin Compose (`docker compose version` deve funcionar)
- Bash (Linux, macOS, WSL ou Git Bash no Windows). Sem Bash, veja "Rodar sem o script" abaixo.
- Acesso à internet na primeira execução, para baixar a imagem `python:3.12-slim`.
  Não há nenhuma outra dependência: o código usa só a biblioteca padrão do Python.

## Passo a passo

```bash
git clone https://github.com/thainapontes/Containers-e-Nuvens
cd Containers-e-Nuvens

# 1) Reproduzir a falha (cerca de 1 minuto e meio)
./rodar.sh prof_sem_mitigacao off

# 2) Rodar com a mitigação (validação do limite + última configuração boa)
./rodar.sh prof_com_mitigacao on

# 3) Comparar as duas execuções
docker run --rm -v "$PWD":/w -w /w python:3.12-slim \
  python analisar.py logs/prof_sem_mitigacao logs/prof_com_mitigacao
```

> Use nomes novos (como `prof_...`). As pastas de `logs/` que já existem no repositório são
> execuções citadas no laudo ou anteriores a ele, e o script se recusa a sobrescrevê-las.

Cada execução cria `logs/<nome>/` com:

| Arquivo | Conteúdo |
|---|---|
| `gerador.log` | cada arquivo publicado (bom/ruim, nº de features), nós atualizados, rollback |
| `proxy.log` | cada configuração carregada, `PANICO` ou `REJEITADO` |
| `cliente.csv` | uma linha por requisição: horário (epoch), status HTTP, latência |
| `compose.log` | saída completa do `docker compose up` |
| `saude.log` | estado do healthcheck do proxy (`starting`/`healthy`/`unhealthy`), uma amostra por segundo |
| `config.txt` | data, parâmetros e versão do Docker |
| `metricas.txt` | métricas calculadas por `analisar.py` a partir dos arquivos acima |

O script se recusa a sobrescrever uma pasta de logs que já existe, para preservar as saídas brutas.
Para repetir, use outro nome: `./rodar.sh sem_mitigacao_2 off`.

### O que o professor deve ver

- **Sem mitigação**: `proxy.log` mostra linhas `PANICO ... n=240 limite=200`, e o `cliente.csv`
  tem respostas `500` que somem e voltam (oscilação) até o `ROLLBACK` do gerador.
- **Com mitigação**: `proxy.log` mostra `REJEITADO`, e o cliente só recebe `200`.
- **Nos dois casos**: `saude.log` mostra o proxy `healthy` o tempo todo, inclusive durante os `500`.

## Rodar sem o script (PowerShell)

```powershell
$env:RUN_ID="prof_sem_mitigacao"; $env:MITIGACAO="off"
mkdir logs\$env:RUN_ID
docker compose up --abort-on-container-exit --exit-code-from cliente
docker compose down
docker run --rm -v "${PWD}:/w" -w /w python:3.12-slim python analisar.py logs/$env:RUN_ID
```

Sem o script, o `saude.log` não é gravado (a métrica do healthcheck sai como `sem saude.log`).

## Arquitetura

```
             rede "interna" (internal: true)        rede "publica"
 [gerador] ─────────────────────────────── [proxy] ─────────────────── [cliente]
  porta 8000                                porta 8080
  /features.json                            GET /  -> 200 | 500 | 503
```

| Container | Representa no sistema real |
|---|---|
| `gerador` | consulta ao cluster ClickHouse + job que gera o *feature file* do Bot Management. Simula 5 nós que recebem a mudança de permissão um de cada vez; um nó atualizado devolve as colunas em dobro (bancos `default` e `r0`). |
| `proxy` | proxy central (FL2) com o módulo Bot Management: memória pré-alocada para 200 features, igual ao limite do artigo. |
| `cliente` | tráfego de usuários passando pela Cloudflare (10 req/s). |

## Parâmetros

Os parâmetros ficam em `docker-compose.yml`. A linha do tempo está comprimida: o que no caso
real levou horas aqui leva segundos.

| Parâmetro | Padrão | Significado |
|---|---|---|
| `N_FEATURES` | 120 | features no arquivo bom (o arquivo ruim tem o dobro) |
| `LIMITE` | 200 | limite pré-alocado no proxy |
| `T_MUDANCA` | 15 s | quando a mudança de permissão começa |
| `PASSO_ROLLOUT` | 6 s | intervalo entre nós atualizados |
| `INTERVALO_GERACAO` | 3 s | intervalo entre gerações do arquivo |
| `T_ROLLBACK` | 60 s | quando a geração é parada e o arquivo bom é reinjetado |
| `MITIGACAO` | off | `on` liga a validação do limite com última configuração boa |
| `SEED` | 42 | semente do sorteio de nós (mesma semente = mesma sequência de arquivos) |

Use a mesma `SEED` nas execuções com e sem mitigação para que as duas recebam exatamente a
mesma sequência de arquivos bons e ruins.

## Laudo e execuções citadas

- Laudo em PDF: [`laudo/laudo.pdf`](laudo/laudo.pdf) (fonte em `laudo/laudo.html`).
- Execuções citadas no laudo (saídas brutas, não editadas). As pastas sem `_v2`
  (`sem_mitigacao`, `com_mitigacao`, `sem_mitigacao_seed7`, `sem_mitigacao_seed2025`) são da
  versão anterior do laudo, feitas antes do `saude.log`, e ficaram como histórico:

| Pasta | Comando |
|---|---|
| `logs/sem_mitigacao_v2/` | `./rodar.sh sem_mitigacao_v2 off` (`SEED` 42) |
| `logs/com_mitigacao_v2/` | `./rodar.sh com_mitigacao_v2 on` (`SEED` 42) |
| `logs/comparacao_sem_mitigacao_v2_vs_com_mitigacao_v2.txt` | `python analisar.py logs/sem_mitigacao_v2 logs/com_mitigacao_v2` |
| `logs/sem_mitigacao_seed7_v2/` | `SEED=7 ./rodar.sh sem_mitigacao_seed7_v2 off` |
| `logs/sem_mitigacao_seed2025_v2/` | `SEED=2025 ./rodar.sh sem_mitigacao_seed2025_v2 off` |
| `logs/parte_d/teste_lote_worker.txt` | worker do projeto `Marketplace-da-economia-criativa` com `LOTE=cinco` e `LOTE=5` (Parte D) |
| `logs/parte_d/teste_port_env.txt` | `env.js` do mesmo projeto com `PORT` inválida; script em `logs/parte_d/teste_porta.mjs` (Parte D) |

## Estrutura

```
docker-compose.yml   gerador/gerador.py   proxy/proxy.py   cliente/cliente.py
analisar.py          rodar.sh             logs/            laudo/   IA.md
```
