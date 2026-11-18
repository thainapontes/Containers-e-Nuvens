"""
CLIENTE — representa o tráfego dos usuários passando pela Cloudflare.
Faz uma requisição a cada INTERVALO_MS durante DURACAO segundos e grava
cada resposta em cliente.csv (epoch, status, latência).
"""
import os
import time
import urllib.error
import urllib.request

PROXY_URL = os.getenv("PROXY_URL", "http://proxy:8080/")
INTERVALO_MS = float(os.getenv("INTERVALO_MS", "100"))
DURACAO = float(os.getenv("DURACAO", "80"))
LOG_DIR = os.getenv("LOG_DIR", "/logs")

os.makedirs(LOG_DIR, exist_ok=True)
caminho = os.path.join(LOG_DIR, "cliente.csv")

with open(caminho, "w") as f:
    f.write("epoch,status,latencia_ms\n")
    inicio = time.time()
    proxima = time.monotonic()
    while time.time() - inicio < DURACAO:
        t0 = time.time()
        try:
            with urllib.request.urlopen(PROXY_URL, timeout=1) as r:
                status = str(r.status)
        except urllib.error.HTTPError as e:
            status = str(e.code)
        except Exception as e:
            status = "ERR_" + type(e).__name__
        lat = (time.time() - t0) * 1000
        f.write(f"{t0:.3f},{status},{lat:.1f}\n")
        f.flush()
        proxima += INTERVALO_MS / 1000
        espera = proxima - time.monotonic()
        if espera > 0:
            time.sleep(espera)

print(f"cliente terminou: {caminho}", flush=True)
