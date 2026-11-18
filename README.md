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
./rodar.sh sem_mitigacao off

# 2) Rodar com a mitigação (validação do limite + última configuração boa)
./rodar.sh com_mitigacao on

# 3) Comparar as duas execuções
docker run --rm -v "$PWD":/w -w /w python:3.12-slim \
  python analisar.py logs/sem_mitigacao logs/com_mitigacao
```

Cada execução cria `logs/<nome>/` com:

| Arquivo | Conteúdo |
|---|---|
| `gerador.log` | cada arquivo publicado (bom/ruim, nº de features), nós atualizados, rollback |
| `proxy.log` | cada configuração carregada, `PANICO` ou `REJEITADO` |
| `cliente.csv` | uma linha por requisição: horário (epoch), status HTTP, latência |
| `compose.log` | saída completa do `docker compose up` |
| `config.txt` | data, parâmetros e versão do Docker |
| `metricas.txt` | métricas calculadas por `analisar.py` a partir dos arquivos acima |

O script se recusa a sobrescrever uma pasta de logs que já existe, para preservar as saídas brutas.
Para repetir, use outro nome: `./rodar.sh sem_mitigacao_2 off`.

### O que o professor deve ver

- **Sem mitigação**: `proxy.log` mostra linhas `PANICO ... n=240 limite=200`, e o `cliente.csv`
  tem respostas `500` que somem e voltam (oscilação) até o `ROLLBACK` do gerador.
- **Com mitigação**: `proxy.log` mostra `REJEITADO`, e o cliente só recebe `200`.

## Rodar sem o script (PowerShell)

```powershell
$env:RUN_ID="sem_mitigacao"; $env:MITIGACAO="off"
mkdir logs\$env:RUN_ID
docker compose up --abort-on-container-exit --exit-code-from cliente
docker compose down
docker run --rm -v "${PWD}:/w" -w /w python:3.12-slim python analisar.py logs/$env:RUN_ID
```

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

## Estrutura

```
docker-compose.yml   gerador/gerador.py   proxy/proxy.py   cliente/cliente.py
analisar.py          rodar.sh             logs/            laudo/   IA.md
```
