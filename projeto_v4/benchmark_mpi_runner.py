"""
benchmark_mpi_runner.py — Executado via mpiexec pelo run_all.py

Inicializa o ambiente MPI UMA VEZ e executa N repetições do filtro
dentro desse contexto. Isso evita overhead de cold start por medição.

Uso (pelo run_all.py — não chamar manualmente):
    mpiexec -n <N> python benchmark_mpi_runner.py <imagem.jpg> <filtro> <repeticoes>

Saída: JSON com lista de tempos (apenas processo rank 0)
"""

import sys
import json
import time
import numpy as np
from mpi4py import MPI
from PIL import Image

# ── importa funções de chunk ────────────────────────────────────────────────────
from filtro_media import filtro_media_chunk
from filtro_mediana import filtro_mediana_chunk

CHUNK_FUNCS = {
    "media":   filtro_media_chunk,
    "mediana": filtro_mediana_chunk,
}


def executar_filtro_paralelo(img_array, filtro_func, comm):
    """Aplica filtro em paralelo e retorna tempo medido no rank 0."""
    rank = comm.Get_rank()
    size = comm.Get_size()

    altura, largura, canais = img_array.shape

    linhas_por_proc = altura // size
    resto = altura % size

    inicio = rank * linhas_por_proc + min(rank, resto)
    fim = inicio + linhas_por_proc + (1 if rank < resto else 0)

    halo_inicio = max(0, inicio - 1)
    halo_fim = min(altura, fim + 1)

    chunk_com_halo = img_array[halo_inicio:halo_fim]
    tem_acima = (halo_inicio < inicio)
    tem_abaixo = (halo_fim > fim)

    # Barreira para sincronizar antes de medir
    comm.Barrier()
    t0 = time.perf_counter()

    chunk_filtrado = filtro_func(chunk_com_halo, tem_acima, tem_abaixo)

    offset_local = inicio - halo_inicio
    resultado_local = chunk_filtrado[offset_local:offset_local + (fim - inicio)]

    resultados = comm.gather(resultado_local, root=0)

    t1 = time.perf_counter()

    return t1 - t0 if rank == 0 else None


def main():
    if len(sys.argv) < 4:
        sys.exit(1)

    imagem_path = sys.argv[1]
    filtro_nome = sys.argv[2]
    repeticoes = int(sys.argv[3])

    if filtro_nome not in CHUNK_FUNCS:
        sys.exit(1)

    filtro_func = CHUNK_FUNCS[filtro_nome]

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    if rank == 0:
        img = Image.open(imagem_path).convert("RGB")
        img_array = np.array(img, dtype=np.uint8)
        shape = img_array.shape
    else:
        shape = None

    # bcast minúsculo para o shape (objeto Python simples)
    shape = comm.bcast(shape, root=0)

    # todos os processos alocam o array antes do Bcast maiúsculo
    if rank != 0:
        img_array = np.empty(shape, dtype=np.uint8)

    # Bcast maiúsculo: buffer numpy direto, sem pickle — requisito da atividade
    comm.Bcast(img_array, root=0)

    tempos = []
    for _ in range(repeticoes):
        tempo = executar_filtro_paralelo(img_array, filtro_func, comm)
        if tempo is not None:
            tempos.append(tempo)

    if rank == 0:
        print(json.dumps(tempos))


if __name__ == "__main__":
    main()
