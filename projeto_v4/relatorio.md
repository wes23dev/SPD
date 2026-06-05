# RELATÓRIO — Atividade Avaliativa: Filtros de Imagem com MPI

**Entrega:** 11/06/2026
**Atividade:** Comparação de Filtros 3×3 (Média vs Mediana) com Paralelização MPI
**Disciplina:** SPD — IFSudeste MG

---

## Resumo Executivo

Este relatório documenta a implementação de dois filtros de imagem (média 3×3 e mediana 3×3) em versão sequencial e paralela com MPI, incluindo benchmark real de speedup e análise de desempenho executado na máquina do grupo.

---

## Resultados da Execução

### Ambiente de execução
- **Imagem:** `teste.jpg` — 800×600 px (RGB)
- **MPI:** Microsoft MPI + mpi4py 4.1.2
- **Python:** 3.13.13
- **Repetições por medição:** 5 (com remoção de outliers por IQR)
- **Processos testados:** 1, 2, 4 e 8

---

### Tabela de Speedup — Filtro de Média 3×3

| Processos | Tempo médio (s) | Speedup | Variância |
|:---------:|----------------:|--------:|----------:|
| 1 (seq)   | 4.1826          | 1.00×   | 0.003773  |
| 2         | 2.3303          | 1.79×   | 0.016002  |
| 4         | 1.8596          | 2.25×   | 0.047505  |
| 8         | 1.4656          | 2.85×   | 0.001736  |

### Tabela de Speedup — Filtro de Mediana 3×3

| Processos | Tempo médio (s) | Speedup | Variância |
|:---------:|----------------:|--------:|----------:|
| 1 (seq)   | 9.2135          | 1.00×   | 0.004978  |
| 2         | 5.2370          | 1.76×   | 0.065035  |
| 4         | 3.4943          | 2.64×   | 0.046304  |
| 8         | 3.1997          | 2.88×   | 0.000688  |

---

### Gráfico de Tempo × Número de Processos

O gráfico `grafico_benchmark.png` mostra a queda no tempo de execução à medida que o número de processos MPI aumenta, para ambos os filtros. A curva descendente confirma o ganho real de paralelização.

---

## REFLITA E ANOTE — Respostas às Perguntas

### 1️⃣ O filtro de mediana paralelo teve speedup maior ou menor que o de média? Por quê?

**Resposta:**

Nos resultados obtidos, o filtro de mediana teve **speedup ligeiramente maior** que o de média em 4 processos (2.64× vs 2.25×), confirmando a teoria. Com 8 processos os speedups convergiram (2.88× vs 2.85×), o que indica que a imagem de 800×600 px começa a ser pequena demais para aproveitar todos os 8 processos sem que o overhead de comunicação MPI pese.

**Justificativa teórica:**

O filtro de mediana é computacionalmente **mais intensivo** que o filtro de média:
- **Filtro de média:** Soma 9 valores e divide por 9 — operação O(1) por pixel
- **Filtro de mediana:** Requer ordenação ou seleção dos 9 valores — operação O(n log n) por pixel

Segundo a **Lei de Amdahl**, quanto maior o trabalho computacional por pixel (fração paralelizável), menor o peso relativo do overhead MPI e maior o speedup potencial:

```
Speedup = 1 / (s + (1-s)/p)
onde: s = fração sequencial, p = número de processos
```

Como a mediana tem `s` menor (overhead MPI representa proporção menor do total), o speedup é superior — especialmente visível em 4 processos nos nossos resultados.

---

### 2️⃣ O que acontece com os pixels nas fronteiras entre processos? O grupo tratou isso? Como?

**Resposta:**

Pixels nas **fronteiras entre processos** precisam dos vizinhos que pertencem a outros processos para calcular o filtro 3×3. Este é o problema clássico de comunicação em processamento de imagens paralelo.

**Solução implementada: Halo (camada de contorno)**

Como a imagem inteira é enviada a todos os processos via `comm.Bcast` antes do processamento, cada processo simplesmente acessa 1 linha extra acima e abaixo de sua faixa — sem necessidade de comunicação adicional durante o cálculo:

```python
halo_inicio = max(0, inicio - 1)
halo_fim    = min(altura, fim + 1)
chunk_com_halo = img_array[halo_inicio:halo_fim]
```

Após processar, apenas as linhas originais do processo são enviadas ao `gather`:

```python
offset_local  = inicio - halo_inicio
resultado_local = chunk_filtrado[offset_local:offset_local + (fim - inicio)]
```

As linhas de halo são usadas somente como entrada (leitura) e descartadas — zero overhead adicional de comunicação durante o processamento.

---

### 3️⃣ Por que foi usado `comm.Bcast` (maiúsculo) e não `comm.bcast` (minúsculo)? O que mudaria no desempenho?

**Resposta:**

| Aspecto | `comm.Bcast` (maiúsculo) | `comm.bcast` (minúsculo) |
|---------|--------------------------|--------------------------|
| Tipo de buffer | NumPy array (in-place) | Qualquer objeto Python |
| Serialização | Não (memória direta) | Sim (pickle) |
| Implementação | Nativa do MPI | Camada Python |
| Overhead | Mínimo | Alto |

O `comm.Bcast` opera diretamente sobre o buffer de memória do array numpy, sem serialização. O `comm.bcast` usa pickle, que serializa o array para bytes, transmite e desserializa — muito mais lento para imagens.

Para uma imagem de 4000×3000 px (~36 MB), a diferença pode ser de segundos vs milissegundos. O uso do `Bcast` maiúsculo é **requisito explícito da atividade** e é a escolha correta para dados de imagem.

---

### 4️⃣ Se o número de processos não divide exatamente a altura da imagem, o que o código faz?

**Resposta:**

O código implementa **divisão balanceada com resto distribuído**:

```python
linhas_por_proc = altura // size
resto = altura % size
inicio = rank * linhas_por_proc + min(rank, resto)
fim = inicio + linhas_por_proc + (1 if rank < resto else 0)
```

Os primeiros `resto` processos recebem uma linha extra cada. Exemplo com altura=10 e 3 processos:

| Processo | inicio | fim | Linhas |
|:--------:|:------:|:---:|:------:|
| 0        | 0      | 4   | 4      |
| 1        | 4      | 7   | 3      |
| 2        | 7      | 10  | 3      |

Nenhuma linha é perdida, o desbalanceamento é de no máximo 1 linha e a solução escala para qualquer combinação de altura × processos.

---

## Estrutura dos Arquivos Entregues

```
📂 projeto_filtros_mpi/
├── filtro_media.py          # Filtro de média 3×3 (sequencial + chunk paralelo)
├── filtro_mediana.py        # Filtro de mediana 3×3 (sequencial + chunk paralelo)
├── benchmark_mpi_runner.py  # Runner MPI (chamado internamente via mpiexec)
├── run_all.py               # Pipeline completa: filtra + benchmark + gráfico
├── main.py                  # Versão sequencial simplificada
├── teste.jpg                # Imagem de teste (800×600 px)
├── README.md                # Documentação técnica
├── COMO_RODAR.md            # Instruções de execução
└── relatorio.md             # Este arquivo
```

---

## Como Reproduzir os Resultados

### Requisitos
```
pip install mpi4py numpy pillow matplotlib
Microsoft MPI instalado (msmpisetup.exe)
```

### Execução
```
# Versão sequencial
C:\Users\WAMar\AppData\Local\Programs\Python\Python313\python.exe main.py

# Benchmark completo com MPI
C:\Users\WAMar\AppData\Local\Programs\Python\Python313\python.exe run_all.py teste.jpg
```

### Saídas geradas
- `saida_media_seq.png` — imagem com filtro de média aplicado
- `saida_mediana_seq.png` — imagem com filtro de mediana aplicado
- `grafico_benchmark.png` — gráfico tempo × processos
- `resultados_benchmark.json` — dados completos em JSON

---

## Conclusões

1. **Mediana paralela speedup ≥ Média paralela:** Confirmado nos resultados reais (2.64× vs 2.25× com 4 processos), alinhado com a Lei de Amdahl.
2. **Halo strategy efetiva:** Zero overhead de comunicação adicional após o `Bcast` inicial — todos os dados necessários já estão locais em cada processo.
3. **`comm.Bcast` vs `comm.bcast`:** O uso do buffer numpy direto é mais eficiente e é requisito da atividade.
4. **Divisão com resto:** Implementação robusta — nenhuma linha perdida, desbalanceamento máximo de 1 linha.
5. **Limite de escala:** Com imagem de 800×600 px, o ganho entre 4 e 8 processos é pequeno (overhead MPI passa a competir com o trabalho computacional), o que é esperado e demonstra o comportamento previsto pela Lei de Amdahl.

---

**Relatório preparado para entrega: 11/06/2026**
