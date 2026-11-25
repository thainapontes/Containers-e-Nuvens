"""
PROXY — representa o proxy central da Cloudflare (FL2) com o módulo Bot Management.

- Busca o feature file no gerador a cada POLL segundos (propagação).
- Pré-aloca LIMITE posições para as features (no artigo: limite 200, ~60 em uso).
- MITIGACAO=off: copia o arquivo para as posições sem checar o tamanho. Se passar do
  limite, estoura (IndexError, o equivalente ao unwrap() que entrou em pânico) e o
  módulo fica quebrado: toda requisição recebe 500 até chegar um arquivo bom.
- MITIGACAO=on : valida o tamanho ANTES de aplicar. Arquivo inválido é rejeitado e o
  proxy continua com a última configuração boa (last-known-good).
"""
import json
import os
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LIMITE = int(os.getenv("LIMITE", "200"))
MITIGACAO = os.getenv("MITIGACAO", "off").lower() == "on"
GERADOR_URL = os.getenv("GERADOR_URL", "http://gerador:8000/features.json")
POLL = float(os.getenv("POLL", "1"))
LOG_DIR = os.getenv("LOG_DIR", "/logs")
PORTA = int(os.getenv("PORTA", "8080"))

os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, "proxy.log")

# estado compartilhado entre a thread de recarga e as threads de requisição
lock = threading.Lock()
estado = {"status": "sem_config", "versao": None, "slots": [None] * LIMITE, "n": 0}


def log(evento, **campos):
    extra = " ".join(f"{k}={v}" for k, v in campos.items())
    linha = f"{time.time():.3f} {evento} {extra}".strip()
    print(linha, flush=True)
    with open(LOG_PATH, "a") as f:
        f.write(linha + "\n")


def aplicar(cfg):
    versao, features = cfg["versao"], cfg["features"]
    n = len(features)
    if MITIGACAO and n > LIMITE:
        with lock:
            mantida = estado["versao"]   # lida sob o lock, como no caminho CARREGADO
        log("REJEITADO", versao=versao, n=n, limite=LIMITE, mantendo_versao=mantida)
        return
    with lock:
        try:
            slots = [None] * LIMITE          # memória pré-alocada
            for i, f in enumerate(features):
                slots[i] = f                 # estoura se n > LIMITE
            estado.update(status="ok", versao=versao, slots=slots, n=n)
            log("CARREGADO", versao=versao, n=n)
        except IndexError:
            estado.update(status="panico", versao=versao)
            log("PANICO", versao=versao, n=n, limite=LIMITE,
                erro="IndexError_alem_do_limite_pre_alocado")


def recarregar():
    log("INICIO", limite=LIMITE, mitigacao="on" if MITIGACAO else "off", poll=POLL)
    ultima_vista = None
    while True:
        try:
            with urllib.request.urlopen(GERADOR_URL, timeout=2) as r:
                cfg = json.loads(r.read())
            if cfg["versao"] != ultima_vista:
                ultima_vista = cfg["versao"]
                aplicar(cfg)
        except Exception as e:  # gerador fora do ar: mantém o que tem
            log("ERRO_BUSCA", erro=type(e).__name__)
        time.sleep(POLL)


class Handler(BaseHTTPRequestHandler):
    def responder(self, codigo, corpo):
        dados = json.dumps(corpo).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def do_GET(self):
        if self.path == "/health":
            # healthcheck de "processo vivo", como a maioria dos healthchecks
            return self.responder(200, {"vivo": True})
        with lock:
            st, v, n = estado["status"], estado["versao"], estado["n"]
        if st == "ok":
            score = n % 100  # "bot score" fictício calculado com as features
            return self.responder(200, {"bot_score": score, "versao_config": v})
        if st == "panico":
            return self.responder(500, {"erro": "bot module panicked", "versao_config": v})
        return self.responder(503, {"erro": "sem configuracao"})

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    threading.Thread(target=recarregar, daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0", PORTA), Handler).serve_forever()
