"""
GERADOR — representa o job que gera o "feature file" do Bot Management
a partir de uma consulta num cluster ClickHouse.

Linha do tempo (segundos desde que o container sobe, tudo configurável):
  0 .. T_MUDANCA         : todos os nós antigos -> arquivo bom (N_FEATURES features)
  T_MUDANCA ..           : a mudança de permissão é aplicada nó a nó (rollout gradual);
                           a cada PASSO_ROLLOUT segundos mais um nó passa a devolver
                           linhas duplicadas (banco 'default' + banco 'r0')
  a cada INTERVALO_GERACAO: um nó aleatório roda a consulta e o arquivo é publicado
                           -> se o nó já foi atualizado, o arquivo sai DOBRADO
  T_ROLLBACK             : operadores param a geração e publicam a última versão boa

Serve o arquivo atual em http://gerador:8000/features.json
"""
import json
import os
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

N_FEATURES = int(os.getenv("N_FEATURES", "120"))
N_NOS = int(os.getenv("N_NOS", "5"))
T_MUDANCA = float(os.getenv("T_MUDANCA", "15"))
PASSO_ROLLOUT = float(os.getenv("PASSO_ROLLOUT", "6"))
INTERVALO_GERACAO = float(os.getenv("INTERVALO_GERACAO", "3"))
T_ROLLBACK = float(os.getenv("T_ROLLBACK", "60"))
SEED = int(os.getenv("SEED", "42"))
LOG_DIR = os.getenv("LOG_DIR", "/logs")
PORTA = int(os.getenv("PORTA", "8000"))

os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, "gerador.log")
rng = random.Random(SEED)
lock = threading.Lock()
atual = {"versao": 0, "features": []}


def log(evento, **campos):
    extra = " ".join(f"{k}={v}" for k, v in campos.items())
    linha = f"{time.time():.3f} {evento} {extra}".strip()
    print(linha, flush=True)
    with open(LOG_PATH, "a") as f:
        f.write(linha + "\n")


def consulta(no_atualizado):
    """Simula SELECT name, type FROM system.columns WHERE table='http_requests_features'
    sem filtrar o banco. Nó atualizado também enxerga as colunas do banco r0."""
    linhas = [{"db": "default", "name": f"feature_{i:03d}", "type": "Float64"}
              for i in range(N_FEATURES)]
    if no_atualizado:
        linhas += [{"db": "r0", "name": f"feature_{i:03d}", "type": "Float64"}
                   for i in range(N_FEATURES)]
    # o gerador "esquece" a coluna db, como a consulta real
    return [{"name": l["name"], "type": l["type"]} for l in linhas]


def publicar(features, **info):
    with lock:
        atual["versao"] += 1
        atual["features"] = features
        v = atual["versao"]
    log("PUBLICADO", versao=v, n=len(features), **info)


def ciclo():
    inicio = time.time()
    log("INICIO", n_features=N_FEATURES, n_nos=N_NOS, t_mudanca=T_MUDANCA,
        passo_rollout=PASSO_ROLLOUT, intervalo=INTERVALO_GERACAO,
        t_rollback=T_ROLLBACK, seed=SEED)
    nos = [False] * N_NOS
    ultimo_bom = consulta(False)
    publicar(ultimo_bom, no=0, tipo="bom")
    proxima_geracao = inicio + INTERVALO_GERACAO
    proximo_no = inicio + T_MUDANCA
    mudanca_logada = False
    while True:
        agora = time.time()
        t = agora - inicio
        if t >= T_ROLLBACK:
            # parar a geração e reinjetar a última versão boa conhecida
            publicar(ultimo_bom, no="-", tipo="bom", motivo="rollback")
            log("ROLLBACK", t=f"{t:.1f}")
            log("GERACAO_PARADA")
            return
        if agora >= proximo_no and not all(nos):
            if not mudanca_logada:
                log("MUDANCA_INICIADA", t=f"{t:.1f}")
                mudanca_logada = True
            i = nos.index(False)
            nos[i] = True
            log("NO_ATUALIZADO", no=i, atualizados=f"{sum(nos)}/{N_NOS}")
            proximo_no = agora + PASSO_ROLLOUT
        if agora >= proxima_geracao:
            no = rng.randrange(N_NOS)
            features = consulta(nos[no])
            tipo = "ruim" if nos[no] else "bom"
            if tipo == "bom":
                ultimo_bom = features
            publicar(features, no=no, tipo=tipo)
            proxima_geracao = agora + INTERVALO_GERACAO
        time.sleep(0.05)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            corpo = b"ok"
        elif self.path == "/features.json":
            with lock:
                corpo = json.dumps(atual).encode()
        else:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, *args):
        pass  # sem log por requisição


if __name__ == "__main__":
    threading.Thread(target=ciclo, daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0", PORTA), Handler).serve_forever()
