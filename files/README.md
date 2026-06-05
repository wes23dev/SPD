# Atividade Avaliativa — Filtros de Imagem com MPI
**Entrega: 11/06/2026 | SPD — IFSudeste MG**

---

## Estrutura dos Arquivos

```
filtro_media.py            # Filtro de média 3x3 (sequencial + chunk paralelo)
filtro_mediana.py          # Filtro de mediana 3x3 (sequencial + chunk paralelo)
benchmark_mpi_runner.py    # Runner MPI (chamado internamente pelo benchmark)
run_all.py                 # Pipeline completa: filtra + benchmark + gráfico
README.md                  # Este arquivo
```

---

## Como Executar

### Requisitos
```bash
pip install mpi4py numpy pillow matplotlib
# OpenMPI ou MPICH instalado e mpiexec no PATH
```

### Execução completa (recomendado)
```bash
python run_all.py sua_imagem.jpg
```

Isso irá:
1. Aplicar filtro de média e mediana sequencialmente e salvar as imagens
2. Executar benchmark com 1, 2, 4 e 8 processos MPI para cada filtro
3. Remover outliers via IQR e calcular speedup e variância
4. Exibir tabela de speedup no terminal
5. Gerar `grafico_benchmark.png` (tempo × número de processos)
6. Salvar `resultados_benchmark.json`

### Execução manual dos filtros
```bash
# Sequencial
python filtro_media.py entrada.jpg saida_media.jpg
python filtro_mediana.py entrada.jpg saida_mediana.jpg

# Paralelo (exemplo com 4 processos)
mpiexec -n 4 python -c "
from mpi4py import MPI
from filtro_media import media_paralelo
media_paralelo('entrada.jpg', 'saida_media_4p.jpg')
"
```

---

## Decisões de Implementação

### Imagem escolhida
Recomenda-se uma imagem grande (≥ 2000×2000 px) para que a paralelização seja
relevante. Imagens pequenas têm overhead MPI dominante e o speedup será negativo.
Exemplos: foto de paisagem em alta resolução, imagem de satélite, foto RAW convertida.

### Segundo filtro: Mediana 3x3
O filtro de mediana substitui o pixel central pela **mediana** dos 9 vizinhos
(em vez da média). É mais eficaz para remover ruído salt-and-pepper e preserva
bordas melhor que o filtro de média. Computacionalmente é mais pesado (requer
ordenação dos 9 valores), o que torna a paralelização ainda mais relevante.

### Tratamento de fronteiras entre processos
Cada processo recebe um **halo** de 1 linha acima e 1 abaixo de sua fatia.
Isso é possível pois a imagem inteira é enviada via `comm.Bcast` antes da divisão.
Assim, cada processo tem acesso às linhas vizinhas necessárias sem comunicação
extra ponto-a-ponto durante o processamento.

### Por que `comm.Bcast` (maiúsculo) e não `comm.bcast` (minúsculo)?
- `comm.bcast` (minúsculo): usa **pickle** do Python para serializar qualquer objeto.
  É genérico, mas ineficiente para arrays grandes.
- `comm.Bcast` (maiúsculo): opera diretamente sobre um **buffer numpy** (memória
  contígua), sem serialização. É a operação correta para dados de imagem, pois
  evita cópia desnecessária e aproveita a implementação nativa do MPI.
  O desempenho pode ser ordens de magnitude melhor para imagens grandes.

### Benchmark: por que não usar mpiexec por repetição?
O ambiente MPI é inicializado uma única vez por configuração de N processos.
Se inicializássemos via `mpiexec` a cada repetição do teste, o overhead de
inicialização da rede MPI seria incluído no tempo medido — e seria assimétrico
(sequencial não paga esse custo). O `benchmark_mpi_runner.py` resolve isso
executando todas as repetições dentro do mesmo contexto MPI já inicializado.

### E se o número de processos não divide exatamente a altura?
```python
linhas_por_proc = altura // size
resto = altura % size
inicio = rank * linhas_por_proc + min(rank, resto)
fim = inicio + linhas_por_proc + (1 if rank < resto else 0)
```
Os primeiros `resto` processos recebem uma linha a mais. Isso distribui as
linhas restantes de forma balanceada, sem descartar nenhuma linha da imagem.

---

## REFLITA E ANOTE — Respostas

### 1. O filtro de mediana paralelo teve speedup maior ou menor que o de média? Por quê?
O filtro de mediana tende a ter **speedup maior** que o de média. Isso ocorre pois
a mediana exige ordenar 9 elementos por pixel (ou usar algoritmo de seleção),
tornando cada pixel mais custoso computacionalmente. Como o trabalho por pixel é
maior, a proporção do tempo de comunicação MPI em relação ao tempo de cômputo é
menor, resultando em melhor eficiência paralela (lei de Amdahl: quanto maior a
fração paralelizável, maior o speedup potencial).

### 2. O que acontece com os pixels nas fronteiras entre processos? Como foi tratado?
Pixels na borda de cada fatia precisam dos vizinhos que pertencem à fatia do
processo adjacente. A solução adotada é o **halo**: como a imagem inteira é
distribuída via `Bcast` antes do processamento, cada processo simplesmente
acessa 1 linha extra acima e abaixo de sua faixa sem precisar de comunicação
adicional. As linhas de halo são usadas apenas como entrada (leitura) e os
pixels gerados nessas posições são descartados — apenas os pixels da fatia
original do processo são coletados pelo `gather`.

### 3. Por que foi usado `comm.Bcast` e não `comm.bcast`? O que mudaria no desempenho?
`comm.Bcast` (maiúsculo) opera diretamente sobre o buffer de memória do array
numpy, usando a implementação nativa MPI sem overhead de serialização Python.
`comm.bcast` (minúsculo) usa pickle, que serializa o array para bytes Python,
transmite e desserializa — processo muito mais lento para imagens grandes.
Para uma imagem de 4000×3000 px (≈ 34 MB), a diferença pode ser de segundos
vs milissegundos. O uso do `Bcast` é requisito explícito da atividade.

### 4. Se o número de processos não divide exatamente a altura da imagem, o que o código faz?
O código usa divisão com resto: os primeiros `(altura % size)` processos recebem
uma linha extra cada. Por exemplo, com altura=10 e 3 processos:
  - Proc 0: linhas 0–3 (4 linhas)
  - Proc 1: linhas 3–6 (3 linhas — sem a extra pois rank≥resto)
  - Proc 2: linhas 6–9 (3 linhas)
Nenhuma linha é perdida e o desbalanceamento é mínimo (no máximo 1 linha de
diferença entre processos).
