"""
Filtro de Média 3x3 - Versão Sequencial e Paralela com MPI
Atividade Avaliativa - SPD
"""

import numpy as np
from PIL import Image
import time
import sys
import os

# ─── FILTRO DE MÉDIA ───────────────────────────────────────────────────────────

def filtro_media_seq(img_array):
    """Aplica filtro de média 3x3 sequencialmente."""
    altura, largura, canais = img_array.shape
    resultado = np.copy(img_array).astype(np.float64)

    for c in range(canais):
        for i in range(1, altura - 1):
            for j in range(1, largura - 1):
                vizinhanca = img_array[i-1:i+2, j-1:j+2, c]
                resultado[i, j, c] = np.mean(vizinhanca)

    return resultado.astype(np.uint8)


def filtro_media_chunk(chunk, tem_linha_acima, tem_linha_abaixo):
    """
    Aplica filtro de média 3x3 a um chunk (fatia de linhas).
    Linhas de fronteira (primeira/última do chunk) precisam de halo.
    """
    altura, largura, canais = chunk.shape
    resultado = np.copy(chunk).astype(np.float64)

    # Linhas internas ao chunk (sem depender de halo)
    i_inicio = 1 if tem_linha_acima else 1
    i_fim = altura - 1 if tem_linha_abaixo else altura - 1

    for c in range(canais):
        for i in range(i_inicio, i_fim):
            for j in range(1, largura - 1):
                vizinhanca = chunk[i-1:i+2, j-1:j+2, c]
                resultado[i, j, c] = np.mean(vizinhanca)

    return resultado.astype(np.uint8)


def media_paralelo(imagem_path, output_path):
    from mpi4py import MPI

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # Processo 0 carrega e distribui a imagem
    if rank == 0:
        img = Image.open(imagem_path).convert("RGB")
        img_array = np.array(img, dtype=np.uint8)
        shape = img_array.shape
    else:
        img_array = None
        shape = None

    # Broadcast da imagem inteira (operação com maiúscula = buffer numpy)
    shape = comm.bcast(shape, root=0)

    if rank != 0:
        img_array = np.empty(shape, dtype=np.uint8)

    comm.Bcast(img_array, root=0)  # Operação com maiúscula (buffer numpy)

    altura, largura, canais = shape

    # Divisão das linhas entre processos
    linhas_por_proc = altura // size
    resto = altura % size

    # Cada processo calcula seu intervalo de linhas (com halo de 1 linha)
    inicio = rank * linhas_por_proc + min(rank, resto)
    fim = inicio + linhas_por_proc + (1 if rank < resto else 0)

    # Adiciona halo: 1 linha acima e 1 abaixo
    halo_inicio = max(0, inicio - 1)
    halo_fim = min(altura, fim + 1)

    chunk_com_halo = img_array[halo_inicio:halo_fim]

    tem_acima = (halo_inicio < inicio)
    tem_abaixo = (halo_fim > fim)

    chunk_filtrado = filtro_media_chunk(chunk_com_halo, tem_acima, tem_abaixo)

    # Extrai apenas as linhas que pertencem a este processo (sem halo)
    offset_local = inicio - halo_inicio
    resultado_local = chunk_filtrado[offset_local:offset_local + (fim - inicio)]

    # Gather dos resultados no processo 0
    resultados = comm.gather(resultado_local, root=0)

    if rank == 0:
        imagem_final = np.vstack(resultados).astype(np.uint8)
        Image.fromarray(imagem_final).save(output_path)
        return imagem_final

    return None


# ─── EXECUÇÃO DIRETA (sequencial) ─────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python filtro_media.py <entrada.jpg> <saida.jpg>")
        sys.exit(1)

    entrada = sys.argv[1]
    saida = sys.argv[2]

    img = Image.open(entrada).convert("RGB")
    img_array = np.array(img)

    t0 = time.time()
    resultado = filtro_media_seq(img_array)
    t1 = time.time()

    Image.fromarray(resultado).save(saida)
    print(f"Filtro de média sequencial: {t1 - t0:.4f}s")
    print(f"Imagem salva em: {saida}")
