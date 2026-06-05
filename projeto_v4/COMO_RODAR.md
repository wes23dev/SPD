# Como Rodar

## ⚠️ Importante — Use sempre o Python 3.13

No terminal, **nunca use só `python`**, sempre use o caminho completo:

```
C:\Users\WAMar\AppData\Local\Programs\Python\Python313\python.exe
```

---

## Comandos

### Versão sequencial (rápida)
```
C:\Users\WAMar\AppData\Local\Programs\Python\Python313\python.exe main.py
```

### Benchmark completo com MPI
```
C:\Users\WAMar\AppData\Local\Programs\Python\Python313\python.exe run_all.py teste.jpg
```

---

## O que o benchmark gera
- `saida_media_seq.png` — imagem com filtro de média
- `saida_mediana_seq.png` — imagem com filtro de mediana
- `grafico_benchmark.png` — gráfico tempo × processos
- `resultados_benchmark.json` — dados completos em JSON

---

## Requisitos (instalar uma vez)
```
C:\Users\WAMar\AppData\Local\Programs\Python\Python313\python.exe -m pip install numpy pillow matplotlib mpi4py
```
