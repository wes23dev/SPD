import argparse
import concurrent.futures
import hashlib


def encontrar_numero_por_hash(hash_alvo, inicio, fim):
    for i in range(inicio, fim + 1):
        if hashlib.md5(str(i).encode()).hexdigest() == hash_alvo:
            return i
    return None


def gerar_intervalos(limite, workers):
    tamanho = limite // workers
    intervalos = []
    inicio = 1

    for i in range(workers):
        fim = inicio + tamanho - 1
        if i == workers - 1:
            fim = limite
        intervalos.append((inicio, fim))
        inicio = fim + 1

    return intervalos


def buscar_paralelo(hash_alvo, limite, workers, modo):
    intervalos = gerar_intervalos(limite, workers)

    if modo == "process":
        executor_cls = concurrent.futures.ProcessPoolExecutor
    elif modo == "thread":
        executor_cls = concurrent.futures.ThreadPoolExecutor
    else:
        raise ValueError("Modo inválido. Use 'thread' ou 'process'.")

    with executor_cls(max_workers=workers) as executor:
        futures = [executor.submit(encontrar_numero_por_hash, hash_alvo, inicio, fim)
                   for inicio, fim in intervalos]

        for future in concurrent.futures.as_completed(futures):
            resultado = future.result()
            if resultado is not None:
                return resultado

    return None


def main():
    parser = argparse.ArgumentParser(description="Busca paralela de hash MD5 com número de workers configurável.")
    parser.add_argument("--hash", default="f0898af949a373e72a4f6a34b4de9090",
                        help="Hash MD5 alvo para encontrar o número correspondente.")
    parser.add_argument("--limit", type=int, default=10000000,
                        help="Máximo número a testar.")
    parser.add_argument("--workers", type=int, default=12,
                        help="Número de processos/threads a usar.")
    parser.add_argument("--mode", choices=["thread", "process"], default="process",
                        help="Modo de execução: 'thread' ou 'process'.")
    args = parser.parse_args()

    resultado = buscar_paralelo(args.hash, args.limit, args.workers, args.mode)
    print(resultado)


if __name__ == "__main__":
    main()