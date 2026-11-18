# Laudo técnico: incidente da Cloudflare de 18/11/2025

> **Roteiro para a equipe.** As Partes A e B estão rascunhadas a partir do artigo e do código.
> Revisem e reescrevam com as palavras de vocês. Nas Partes C e D, tudo entre `[ ]` precisa
> vir das execuções de vocês (`logs/`) e do projeto de vocês. **Não coloquem nenhum número
> que não esteja em `logs/`.** Limite: 6 páginas no PDF.
>
> Fonte: Cloudflare, "Cloudflare outage on November 18, 2025",
> https://blog.cloudflare.com/18-november-2025-outage/ (todos os horários em UTC).

---

## Parte A: o mecanismo

**Mecanismo em uma frase.** Uma mudança de permissões no ClickHouse fez a consulta que gera o
*feature file* do Bot Management devolver colunas duplicadas; o arquivo dobrou, passou do
limite de 200 features pré-alocado no proxy, o código entrou em pânico e o proxy, que fica no
caminho de todo o tráfego, passou a responder 5xx.

### Linha do tempo

| Horário (UTC) | Evento | Onde está no artigo |
|---|---|---|
| 11:05 | Mudança de controle de acesso no banco é implantada | Tabela final, linha 11:05; seção "The query behaviour change" |
| 11:28 | A mudança chega aos ambientes de clientes; primeiros erros no tráfego HTTP | Tabela final, linha 11:28 |
| 11:31 / 11:35 | Primeiro teste automático detecta o problema (11:31); sala de incidente criada (11:35) | Tabela final, linha 11:32–13:05 |
| (sem horário) | O sistema alterna entre falha e recuperação a cada geração do arquivo (a cada 5 min), até todos os nós do ClickHouse gerarem o arquivo ruim | Seção "The outage" |
| 14:24 | Geração e propagação de novos arquivos interrompidas | Tabela final, linha 14:24 |
| 14:30 | Arquivo correto implantado globalmente; impacto principal resolvido | Tabela final, linha 14:30; introdução |
| 17:06 | Todos os serviços restaurados | Tabela final, linha 17:06 |

> Escolham de 4 a 6 linhas. Observação útil para o laudo: a introdução do artigo diz que as
> falhas começaram às **11:20**, mas a tabela final marca o início do impacto às **11:28**.
> Citem as duas e digam qual usaram.

### Conceito da disciplina: ponto único de falha

O *feature file* é um único artefato, gerado em um único lugar e propagado rapidamente para
**todas** as máquinas da rede. Todas rodam o mesmo código com o mesmo limite fixo, então não há
diversidade: um único arquivo inválido basta para derrubar o tráfego no mundo inteiro. A
redundância de milhares de servidores não ajuda quando todos dependem da mesma entrada e falham
pela mesma razão. O artigo reconhece isso nas ações corretivas, ao propor tratar arquivos
gerados internamente com o mesmo cuidado que a entrada de usuários (seção "Remediation and
follow-up steps").

**Conceito secundário: consistência.** Durante o rollout gradual, nós diferentes do cluster
davam respostas diferentes para a mesma consulta. Por isso o sistema oscilou e a equipe
inicialmente suspeitou de um ataque DDoS.

---

## Parte B: a miniatura

### Diagrama

```
             rede "interna" (internal: true)         rede "publica"
 [gerador] ───────────────────────────────── [proxy] ─────────────────── [cliente]
  5 nós simulados, 1 atualizado              limite pré-alocado = 200     10 req/s
  a cada 6 s; gera arquivo a cada 3 s        MITIGACAO=off|on
```
_(Transformar num diagrama de verdade para o PDF.)_

### Correspondência

| Container | Peça real | Como foi modelada |
|---|---|---|
| `gerador` | Cluster ClickHouse + job de geração do *feature file* | Consulta simulada sem filtro de banco; nó atualizado devolve as linhas de `default` e de `r0`, dobrando o arquivo. Rollout nó a nó. |
| `proxy` | Proxy central FL2 com o módulo Bot Management | Vetor pré-alocado de 200 posições; arquivo maior gera `IndexError` (o equivalente ao `unwrap()` em Rust) e o proxy responde 500. |
| `cliente` | Tráfego de usuários | Requisições a cada 100 ms, cada resposta registrada em `cliente.csv`. |
| rede `interna` | Plano de controle (distribuição de configuração) | O cliente não alcança o gerador. |
| rede `publica` | Plano de dados (tráfego de clientes) | — |

### O que a miniatura não reproduz

| Limitação | Efeito nas conclusões |
|---|---|
| Um proxy só, contra milhares de máquinas que recebem o arquivo em momentos diferentes | A falha na miniatura é instantânea e total. A porcentagem de erro medida é um caso extremo e não representa a falha parcial e progressiva da rede real. |
| O proxy recarrega a configuração sozinho; no caso real foi preciso forçar o reinício do proxy e reiniciar serviços que ficaram em estado ruim até 17:06 | O tempo de recuperação medido é muito menor que o real. Medimos só "arquivo bom de volta → tráfego ok", sem a cauda longa. |
| O rollback acontece num horário programado (`T_ROLLBACK`); no caso real ele dependeu do diagnóstico, atrasado pela suspeita de DDoS e pela queda coincidente da página de status | Não medimos o tempo de diagnóstico humano, que dominou a duração real do incidente. |
| Só o comportamento do FL2 (5xx) foi simulado; no proxy antigo (FL) não houve erro, mas o bot score ficou zero | A miniatura não mostra a falha silenciosa (falsos positivos para clientes que bloqueiam bots), que é mais difícil de detectar. |
| Arquivo bom com 120 features para que o dobro (240) passe do limite; no artigo, ~60 features estavam em uso | A proporção entre uso e limite foi ajustada. A margem real era maior, o que reforça que só uma duplicação grande cruzaria o limite. |
| Sem efeitos secundários: CPU gasta pelos sistemas de debug, Workers KV, Turnstile, backlog de logins no dashboard | Não reproduzimos o efeito manada na volta do tráfego nem as dependências em cascata. |

> Escolham pelo menos 3.

---

## Parte C: o experimento

Comandos: `./rodar.sh sem_mitigacao off` (ver README). Linha do tempo comprimida: uma geração
a cada 3 s, contra 5 min no caso real.

| Métrica | Miniatura | Fonte (log) | Caso real | Fonte (artigo) |
|---|---|---|---|---|
| Tempo até a falha (mudança → 1º erro) | 7.10 s | `logs/sem_mitigacao/metricas.txt` | 11:05 → 11:28 (23 min) | Tabela final |
| Tempo até a falha (1º arquivo ruim → 1º erro) | 0.95 s | idem | não informado | — |
| Tempo até a recuperação (arquivo bom de volta → último erro) | 0.16 s | idem | 14:24 → 14:30 (impacto principal); até 17:06 para tudo | Tabela final |
| Duração do impacto | 38.09 s | idem | 11:28 → 14:30 | Tabela final |
| % de requisições com erro | 40.07 % | idem | não informado em número (só o gráfico de 5xx) | Seção "The outage" |
| Número de oscilações (blocos de erro) | 3 | idem | "recuperava por um período" e voltava a falhar | Seção "The outage" |

**Comparação.** _(Escrever: o que bateu (oscilação, propagação rápida), o que não bate e por
quê, usando a tabela de limitações.)_

**O que saiu diferente do esperado.** _(Escrever a partir do que vocês observarem nos logs.
Olhem, por exemplo, o `proxy.log` e o status do healthcheck durante a falha, a quantidade de
oscilações em execuções com `SEED` diferente, e o tempo entre a publicação do arquivo e o
primeiro erro.)_

---

## Parte D: parecer para a diretora

**Isso pode acontecer com o nosso projeto?** _(Responder sim/não e por quê.)_

**Onde:** `[arquivo do projeto da equipe]`, linhas `[ ]`:
```
[colar o trecho]
```
_(Procurem um lugar onde o projeto carrega configuração, variável de ambiente ou resposta de
outro serviço **sem validar** tamanho ou formato, um `depends_on` sem healthcheck, ou um
healthcheck que só testa se o processo está vivo.)_

**Mitigação implementada:** validação do limite antes de aplicar a configuração, mantendo a
última configuração boa (`proxy/proxy.py`, `MITIGACAO=on`). Corresponde à primeira ação
corretiva do artigo.

| Métrica | Sem mitigação | Com mitigação | Fonte |
|---|---|---|---|
| % de requisições com erro | 40.07 % | 0.00 % | `logs/comparacao_sem_mitigacao_vs_com_mitigacao.txt` |
| Requisições com erro | 321 | 0 | idem |
| Eventos `PANICO` | 11 | 0 | idem |
| Arquivos `REJEITADOS` | 0 | 11 | idem |

**Recomendação final.** _(2 ou 3 frases para a diretora.)_
