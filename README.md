# Trabalho SpeeDup
## Na pasta - 
Trabalho_Speedup_Windows Tendo os resultados no arquivo csv da máquina Windows
## E na pasta-
Trabalho_Speedup_Linux Tendo os resultados no arquivo json da máquina Linux 


## REFLITA e ANOTE:

## a)Por que obteve esses resultados?

A diferença de desempenho entre o Programa A e o Programa B deve-se à forma como eles gerenciam os recursos do processador para resolver um problema de alto custo.
A Natureza do Problema: CPU-bound
O nosso processo (calcular múltiplos hashes MD5 e comparar strings) é classificado como CPU-bound. Isso significa que o limitador de velocidade é a capacidade de processamento puro da CPU, onde o  programa gasta a maior parte do tempo realizando cálculos matemáticos.
Programa A (Sequencial): Este programa executa uma tarefa por vez, utilizando apenas um núcleo do processador, assim tendo um tempo de execução maior.
Programa B (Paralelo): Este programa divide o trabalho em vários processos. Isso permite que vários núcleos da CPU trabalhem simultaneamente, reduzindo drasticamente o tempo total de execução.
Embora o Programa B seja mais rápido, o tempo não diminui exatamente na mesma proporção do número de núcleos. Isso acontece devido ao Overhead (custo de gerenciamento). No Python, como é uma linguagem interpretada, existe um custo computacional para:
Criar e destruir novos processos.
Comunicar dados entre esses processos.
Coordenar o que cada núcleo está fazendo.
A escolha por Multiprocessing (processos) em vez de Threads foi fundamental devido ao GIL  (Global Interpreter Lock) O GIL é um "cadeado" (lock) que permite que apenas uma thread execute o código (bytecode) do Python por vez, mesmo que o seu computador tenha vários núcleos de CPU.
O problema das Threads: O GIL garante que apenas uma thread execute código Python por vez dentro de um único processo. Em tarefas de cálculo pesado (CPU-bound), o uso de threads acabaria simulando uma execução sequencial, não aproveitando o poder real do processador.
A solução por Processos: Ao utilizarmos processos (Multiprocessing), cada um possui seu próprio interpretador Python e seu próprio GIL. Isso permite que eles rodem em paralelo de verdade, superando a limitação técnica da linguagem e garantindo a queda no tempo de execução.


## b) A relação do tempo do speedup coletado com os itens abaixo:

## i)Qual o hardware usado? Isso influencia?

Máquina 1: Intel core i5 12450H
Núcleos físicos 8 cores, 12 threads

Máquina 2: Intel Core i5-12450H
Núcleos físicos8 cores, 12 threads

O hardware é o fator mais importante:
se você tem 4 núcleos físicos, usar 8 processos não dobra o ganho;
porque o sistema operacional precisa alternar entre processos e isso gera custo;
o ideal é usar um número de workers próximo ao número de núcleos/threads disponíveis.
processador mais rápido reduz o tempo absoluto de cada hash;



## ii)Qual o sistema operacional usado? Isso influencia?

Máquina 1- Windows

Programa_B_2_processos /speedup /0.66280301
Programa_B_4_processos /speedup /0.42635374
Programa_B_8_processos /speedup /0.47892933

Máquina 2- Linux
 "speedups": {
    "Programa_B_2_threads": 0.9842086437695609,
    "Programa_B_4_threads": 0.9845024061944577,
    "Programa_B_8_threads": 0.8362275831594258
  }


Sim, o sistema operacional influencia diretamente a eficiência do programa, principalmente na forma como os novos processos são criados. Em Python, a biblioteca multiprocessing utiliza diferentes métodos de inicialização dependendo da plataforma, o que impacta o overhead (custo de tempo e memória).
No Linux, o padrão é geralmente o fork.
Como funciona: O sistema operacional cria uma cópia quase instantânea do processo pai. Ele utiliza uma técnica chamada Copy-on-Write (CoW), onde a memória só é realmente duplicada se um dos processos tentar alterá-la.
Vantagem: É extremamente rápido e eficiente. O processo filho já nasce com acesso a quase todas as variáveis e estados do pai sem precisar recarregar tudo.

No Windows (Spawn): O sistema não faz essa cópia. Ele abre um processo novo e "vazio". Esse processo novo tem que carregar o Python do zero, importar as bibliotecas e preparar tudo de novo. Por isso o Windows tem mais overhead.




## iii)Qual a linguagem e recursos da linguagem usados? Haveria diferença se as linguagens fossem diferentes?

Python 
No linux 3.12.3 
No windows 3.7
Recursos- Módulos da biblioteca padrão
argparse
para receber parâmetros pela linha de comando (--workers, --limit, --output, etc.)
hashlib
para calcular MD5 de str(i).encode()
concurrent.futures
em Programa_B.py, usado ProcessPoolExecutor para executar a busca em paralelo
subprocess
em testador.py, para chamar os scripts Python como processos separados e medir tempo
sys
para obter o caminho do executável Python (sys.executable)

time
time.perf_counter() em testador.py para medir tempo de execução com alta precisão
statistics
para calcular mediana e média, e detectar outliers usando IQR em testador.py
csv
para salvar resultados em formato CSV
json
para salvar resultados em formato JSON
pathlib.Path
para construir caminhos de arquivo de forma portátil em testador.py

Python não escala bem com threads para CPU-bound por causa do GIL;
por isso a escolha correta aqui foi também usar processos;
concurrent.futures.ProcessPoolExecutor é uma forma de obter paralelismo real em CPU-bound no Python.

Haveria diferença sim,
C/C++/Rust: seria mais rápido no sequencial e o paralelo também escalaria melhor;
Java/C#: teriam ganho paralelo com menor overhead de inicialização de tarefas;
Python é mais fácil de escrever, mas o throughput absoluto é menor que o de uma linguagem compilada.

## iv)O conjunto de dados influenciou nos resultados (palavras mais frequentes e mais raras)?
Sim, o conjunto de dados influenciou a dinâmica do teste, mas de forma diferente de uma base de dados comum. No problema atual, o "conjunto de dados" é um intervalo numérico de 1 a 10.000.000, o que traz as seguintes características:
Espaço de Busca Uniforme
Diferente de uma lista de nomes ou palavras, onde existem termos mais comuns ("frequentes") ou raros, o intervalo numérico é uniforme.
Sem atalhos por frequência: Não existem números que "aparecem mais vezes". Cada hash MD5 exige o mesmo esforço computacional para ser gerado.
Carga previsível: O esforço é constante do início ao fim do intervalo.
B. A Posição do Alvo e o Tempo de Execução
O tempo total depende diretamente de onde o "número alvo" (aquele que gera o hash que você procura) está localizado:
Alvo no início (perto de 1): Beneficia o programa sequencial e o primeiro worker do paralelo, permitindo um término precoce se houver uma instrução de parada.
Alvo no final (perto de 10 milhões): Força todos os processos a realizarem o trabalho máximo (Busca Exaustiva). É aqui que o Programa B (paralelo) mostra sua maior vantagem.

## v)Por que determinada abordagem obteve melhor desempenho em relação a outra (paralelo x sequencial)?
           A diferença de desempenho entre a abordagem Paralela e a Sequencial se resume à forma como o tempo e os recursos do hardware são gerenciados.

A principal razão do melhor desempenho do paralelo é a sobreposição de tarefas.
Abordagem Sequencial: Trabalha em uma fila única. Se você tem 4 tarefas de 1 minuto, o tempo final será obrigatoriamente 4 minutos, pois a Tarefa 2 só começa quando a Tarefa 1 termina.
Abordagem Paralela: Se você tiver 4 núcleos de CPU, cada núcleo assume uma tarefa ao mesmo tempo. O tempo final cai para 1 minuto (o tempo da tarefa mais longa).
A abordagem paralela vence de forma esmagadora quando o problema é CPU-Bound (limitado pelo processador).
Cálculos matemáticos, renderização de vídeo e geração de hashes (como o MD5) exigem ciclos intensos de CPU.
Enquanto o programa sequencial deixa os outros núcleos do seu computador ociosos (gastando energia sem produzir), o paralelo "estressa" o hardware para entregar o resultado mais rápido.

## vi)Onde foi possível aumentar a vazão na sua proposta?

A vazão foi aumentada ao usar paralelismo por processos e dividir a carga.
Mas o código não está otimizado para interromper os workers restantes, então o ganho vem do paralelismo, não de uma redução total de trabalho.

Cada processo (worker) faz um bloco diferente do trabalho, o que utiliza múltiplos núcleos da CPU em vez de apenas um.




