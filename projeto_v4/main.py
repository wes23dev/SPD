#!/usr/bin/env python
"""
main.py - Programa principal
Executa benchmark dos filtros de imagem
"""
import sys
import os
import time
import numpy as np
from PIL import Image
from filtro_media import filtro_media_seq
from filtro_mediana import filtro_mediana_seq

def main():
    print("=" * 50)
    print("BENCHMARK DE FILTROS DE IMAGEM")
    print("=" * 50)
    print()

    img_path = "teste.jpg"

    if not os.path.exists(img_path):
        print(f"Arquivo não encontrado: {img_path}")
        sys.exit(1)

    # Carregar imagem
    print(f"Carregando: {img_path}")
    img = Image.open(img_path).convert("RGB")
    img_array = np.array(img)
    print(f"Tamanho: {img_array.shape[1]}×{img_array.shape[0]} px\n")

    # Filtro de Média
    print("Executando filtro de média...")
    t0 = time.perf_counter()
    resultado_media = filtro_media_seq(img_array)
    t_media = time.perf_counter() - t0
    Image.fromarray(resultado_media).save("saida_media.png")
    print(f"✓ Tempo: {t_media:.4f}s")
    print(f"✓ Salvo: saida_media.png\n")

    # Filtro de Mediana
    print("Executando filtro de mediana...")
    t0 = time.perf_counter()
    resultado_mediana = filtro_mediana_seq(img_array)
    t_mediana = time.perf_counter() - t0
    Image.fromarray(resultado_mediana).save("saida_mediana.png")
    print(f"✓ Tempo: {t_mediana:.4f}s")
    print(f"✓ Salvo: saida_mediana.png\n")

    # Resultado
    print("─" * 50)
    print(f"Filtro de Média:   {t_media:.4f}s")
    print(f"Filtro de Mediana: {t_mediana:.4f}s")
    print("─" * 50)

if __name__ == "__main__":
    main()
