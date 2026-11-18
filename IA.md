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
**O que aconteceu:** _(preencher)_
**Como descobrimos:** _(preencher: comando e saída)_
**Correção:** _(preencher: arquivo e o que mudou)_

### Erro 2
**O que aconteceu:** _(preencher)_
**Como descobrimos:** _(preencher)_
**Correção:** _(preencher)_
