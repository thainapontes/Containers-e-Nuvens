"""
Calcula as métricas de uma ou mais execuções a partir dos logs brutos.

Uso:
  python analisar.py logs/sem_mitigacao
  python analisar.py logs/sem_mitigacao logs/com_mitigacao   # também gera a comparação

Saídas (para citar no laudo):
  logs/<execucao>/metricas.txt  (usa saude.log, se existir, para o estado do healthcheck)
  logs/comparacao_<a>_vs_<b>.txt   (quando duas execuções são passadas)
"""
import csv
import os
import sys


def ler_eventos(caminho):
    eventos = []
    if not os.path.exists(caminho):
        return eventos
    with open(caminho) as f:
        for linha in f:
            partes = linha.split()
            if len(partes) < 2:
                continue
            campos = dict(p.split("=", 1) for p in partes[2:] if "=" in p)
            eventos.append((float(partes[0]), partes[1], campos))
    return eventos


def primeiro(eventos, nome, **filtro):
    for t, ev, c in eventos:
        if ev == nome and all(c.get(k) == v for k, v in filtro.items()):
            return t
    return None


def contar(eventos, nome):
    return sum(1 for _, ev, _ in eventos if ev == nome)


def analisar(pasta):
    ger = ler_eventos(os.path.join(pasta, "gerador.log"))
    prx = ler_eventos(os.path.join(pasta, "proxy.log"))
    with open(os.path.join(pasta, "cliente.csv")) as f:
        reqs = [(float(r["epoch"]), r["status"]) for r in csv.DictReader(f)]

    t_mudanca = primeiro(ger, "MUDANCA_INICIADA")
    t_ruim = primeiro(ger, "PUBLICADO", tipo="ruim")
    t_rollback = primeiro(ger, "ROLLBACK")
    t_panico = primeiro(prx, "PANICO")

    total = len(reqs)
    erros = [t for t, s in reqs if s != "200"]
    n_erros = len(erros)

    # blocos de erro consecutivos (cada bloco = uma "queda"; vários = oscilação)
    blocos, dentro = 0, False
    for _, s in reqs:
        if s != "200" and not dentro:
            blocos += 1
        dentro = s != "200"

    def seg(x):
        return "n/a" if x is None else f"{x:.2f} s"

    m = {}
    m["requisicoes_total"] = (str(total), "cliente.csv")
    m["requisicoes_com_erro"] = (str(n_erros), "cliente.csv")
    m["porcentagem_erro"] = (f"{100 * n_erros / total:.2f} %" if total else "n/a", "cliente.csv")
    if t_ruim and t_rollback:
        janela = [s for t, s in reqs if t_ruim <= t <= t_rollback]
        e_j = sum(1 for s in janela if s != "200")
        m["porcentagem_erro_entre_1o_arquivo_ruim_e_rollback"] = (
            f"{100 * e_j / len(janela):.2f} % ({e_j}/{len(janela)})" if janela else "n/a",
            "cliente.csv + gerador.log")
    m["blocos_de_erro (oscilacoes)"] = (str(blocos), "cliente.csv")
    m["arquivos_ruins_publicados"] = (
        str(sum(1 for _, ev, c in ger if ev == "PUBLICADO" and c.get("tipo") == "ruim")),
        "gerador.log")
    m["eventos_PANICO_no_proxy"] = (str(contar(prx, "PANICO")), "proxy.log")
    m["arquivos_REJEITADOS_pelo_proxy"] = (str(contar(prx, "REJEITADO")), "proxy.log")
    m["tempo_ate_falha (mudanca -> 1o erro)"] = (
        seg(erros[0] - t_mudanca) if erros and t_mudanca else "sem erro",
        "gerador.log MUDANCA_INICIADA + cliente.csv")
    m["tempo_ate_falha (1o arquivo ruim publicado -> 1o erro)"] = (
        seg(erros[0] - t_ruim) if erros and t_ruim else "sem erro",
        "gerador.log PUBLICADO tipo=ruim + cliente.csv")
    m["propagacao (1o arquivo ruim -> PANICO no proxy)"] = (
        seg(t_panico - t_ruim) if t_panico and t_ruim else "n/a",
        "gerador.log + proxy.log")
    if erros and t_rollback:
        rec = erros[-1] - t_rollback
        m["tempo_ate_recuperacao (rollback -> ultimo erro)"] = (
            seg(rec) if rec >= 0 else f"ultimo erro foi {seg(-rec)} ANTES do rollback",
            "gerador.log ROLLBACK + cliente.csv")
    else:
        m["tempo_ate_recuperacao (rollback -> ultimo erro)"] = ("sem erro", "cliente.csv")
    m["duracao_do_impacto (1o erro -> ultimo erro)"] = (
        seg(erros[-1] - erros[0]) if erros else "sem erro", "cliente.csv")
    # saude.log (gravado pelo rodar.sh): estado do healthcheck do proxy, 1 amostra por segundo
    saude = ler_eventos(os.path.join(pasta, "saude.log"))
    if not saude:
        m["healthcheck_do_proxy_durante_o_impacto"] = ("sem saude.log", "saude.log")
    elif not erros:
        m["healthcheck_do_proxy_durante_o_impacto"] = ("sem erro", "saude.log")
    else:
        janela = [st for t, st, _ in saude if int(erros[0]) <= t <= erros[-1]]
        cont = {st: janela.count(st) for st in sorted(set(janela))}
        m["healthcheck_do_proxy_durante_o_impacto"] = (
            " ".join(f"{k}={v}" for k, v in cont.items()) + f" (de {len(janela)} amostras)",
            "saude.log + cliente.csv")

    largura = max(len(k) for k in m)
    linhas = [f"Execucao: {pasta}", ""]
    linhas += [f"{k.ljust(largura)}  {v:<32} fonte: {fonte}" for k, (v, fonte) in m.items()]
    texto = "\n".join(linhas) + "\n"
    # não sobrescreve: metricas.txt faz parte das saídas brutas da execução
    destino = os.path.join(pasta, "metricas.txt")
    if os.path.exists(destino):
        print(f"{destino} ja existe; mantido sem alteracao")
    else:
        with open(destino, "w") as f:
            f.write(texto)
    print(texto)
    return m


def main():
    pastas = [p.rstrip("/") for p in sys.argv[1:]]
    if not pastas:
        print(__doc__)
        sys.exit(1)
    resultados = {p: analisar(p) for p in pastas}
    if len(pastas) >= 2:
        a, b = pastas[0], pastas[1]
        nome = f"comparacao_{os.path.basename(a)}_vs_{os.path.basename(b)}.txt"
        destino = os.path.join(os.path.dirname(a) or ".", nome)
        chaves = list(resultados[a])
        largura = max(len(k) for k in chaves)
        linhas = [f"{'metrica'.ljust(largura)}  {os.path.basename(a):<34} {os.path.basename(b)}"]
        for k in chaves:
            va = resultados[a][k][0]
            vb = resultados[b].get(k, ("n/a",))[0]
            linhas.append(f"{k.ljust(largura)}  {va:<34} {vb}")
        texto = "\n".join(linhas) + "\n"
        print(texto)
        if os.path.exists(destino):
            print(f"{destino} ja existe; mantido sem alteracao")
        else:
            with open(destino, "w") as f:
                f.write(texto)
            print(f"comparacao salva em {destino}")


if __name__ == "__main__":
    main()
