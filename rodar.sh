#!/usr/bin/env bash
# Uso: ./rodar.sh <nome_da_execucao> <off|on>
# Ex.: ./rodar.sh sem_mitigacao off ; ./rodar.sh com_mitigacao on
set -euo pipefail
RUN_ID="${1:?uso: ./rodar.sh <nome_da_execucao> <off|on>}"
MITIGACAO="${2:-off}"
if [ -e "logs/$RUN_ID" ]; then
  echo "logs/$RUN_ID ja existe. Escolha outro nome para nao sobrescrever logs brutos."; exit 1
fi
mkdir -p "logs/$RUN_ID"
# containers gravam em logs/ com o mesmo usuário de quem roda (no Linux, evita arquivos do root)
HOST_UID="$(id -u)"; HOST_GID="$(id -g)"
export RUN_ID MITIGACAO HOST_UID HOST_GID
# saude.log: estado do healthcheck do proxy (starting/healthy/unhealthy) a cada segundo.
# O "docker compose up" não registra mudanças de saúde, então o compose.log não serve para isso.
monitorar_saude() {
  while :; do
    cid="$(docker compose ps -q proxy 2>/dev/null || true)"
    if [ -n "$cid" ]; then
      st="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}sem_healthcheck{{end}}' "$cid" 2>/dev/null || echo parado)"
      echo "$(date +%s) $st"
    fi
    sleep 1
  done
}
monitorar_saude > "logs/$RUN_ID/saude.log" &
MONITOR=$!
# derruba os containers mesmo se o "up" falhar (com set -e o script pararia antes do down)
trap 'kill "$MONITOR" 2>/dev/null || true; docker compose down >/dev/null 2>&1 || true' EXIT
{ echo "data: $(date -u +%Y-%m-%dT%H:%M:%SZ)"; echo "RUN_ID=$RUN_ID"; echo "MITIGACAO=$MITIGACAO"
  echo "SEED=${SEED:-42}"; docker --version; docker compose version; } > "logs/$RUN_ID/config.txt"
docker compose up --abort-on-container-exit --exit-code-from cliente 2>&1 | tee "logs/$RUN_ID/compose.log"
kill "$MONITOR" 2>/dev/null || true
docker compose down
trap - EXIT
docker run --rm --user "$HOST_UID:$HOST_GID" -v "$PWD":/w -w /w python:3.12-slim python analisar.py "logs/$RUN_ID"
