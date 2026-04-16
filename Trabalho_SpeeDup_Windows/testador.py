# Importa argparse para argumentos da linha de comando
import argparse
# Importa csv para salvar dados em formato CSV
import csv
# Importa json para salvar dados em formato JSON
import json
# Importa subprocess para executar comandos externos
import subprocess
# Importa sys para acessar o executável Python
import sys
# Importa statistics para cálculos estatísticos como média e mediana
import statistics
# Importa time para medir tempo de execução
import time
# Importa Path do pathlib para manipular caminhos de arquivos
from pathlib import Path


# Define uma função para executar um comando e medir o tempo
# Recebe uma lista de comandos
def run_program(command):
    # Registra o tempo inicial
    start = time.perf_counter()
    # Executa o comando, suprimindo saída e erro, e verifica se executou sem erro
    subprocess.run(command, shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    # Registra o tempo final
    end = time.perf_counter()
    # Retorna a duração
    return end - start


# Define uma função para detectar e excluir outliers usando o método IQR
# Recebe uma lista de tempos
def reject_outliers(times):
    # Se há menos de 4 tempos, não há outliers suficientes para calcular
    if len(times) < 4:
        return []

    # Ordena os tempos
    sorted_times = sorted(times)
    # Calcula o primeiro quartil (Q1)
    q1 = statistics.median(sorted_times[: len(sorted_times) // 2])
    # Calcula o terceiro quartil (Q3)
    q3 = statistics.median(sorted_times[(len(sorted_times) + 1) // 2 :])
    # Calcula o intervalo interquartil (IQR)
    iqr = q3 - q1
    # Define limites inferior e superior para outliers
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    # Retorna índices dos outliers (começando do 2, pois o primeiro é warmup)
    return [index for index, t in enumerate(times, start=2) if t < lower or t > upper]


# Define uma função para coletar tempos de múltiplas execuções de um cenário
# Recebe nome, comando e número de execuções
def collect_times(name, command, runs):
    # Lista para armazenar todos os tempos
    all_times = []
    # Loop para cada execução
    for i in range(1, runs + 1):
        # Executa o programa e mede o tempo
        duration = run_program(command)
        # Adiciona o tempo à lista
        all_times.append(duration)
        # Imprime o progresso
        print(f"{name} run {i}/{runs}: {duration:.4f}s")

    # Exclui o primeiro tempo como warmup
    warmup_excluded = [1]
    # Considera os tempos após warmup como candidatos
    candidate_times = all_times[1:]
    # Detecta outliers nos candidatos
    outlier_indices = reject_outliers(candidate_times)
    # Inclui apenas tempos não outliers
    included = [t for idx, t in enumerate(candidate_times, start=2) if idx not in outlier_indices]

    # Calcula a média dos tempos incluídos, se houver
    if included:
        mean_time = statistics.mean(included)
    else:
        mean_time = None

    # Retorna um dicionário com os dados coletados
    return {
        "name": name,
        "command": command,
        "all_times": all_times,
        "warmup_excluded": warmup_excluded,
        "outlier_excluded": outlier_indices,
        "included_times": included,
        "mean_time": mean_time,
    }


# Define uma função para salvar dados em JSON
# Recebe os resultados e o caminho do arquivo
def save_json(results, output_path):
    # Abre o arquivo em modo escrita com codificação UTF-8
    with open(output_path, "w", encoding="utf-8") as file:
        # Salva os dados em JSON com indentação
        json.dump(results, file, indent=2)


# Define uma função para salvar dados em CSV
# Recebe resultados, speedups e caminho do arquivo
def save_csv(results, speedups, output_path):
    # Abre o arquivo CSV em modo escrita
    with open(output_path, "w", newline="", encoding="utf-8") as file:
        # Cria um writer CSV
        writer = csv.writer(file)
        # Escreve cabeçalho para os cenários
        writer.writerow(["scenario", "run_index", "duration", "status", "speedup"])
        # Para cada cenário
        for scenario in results:
            name = scenario["name"]
            outlier_indices = set(scenario["outlier_excluded"])
            # Para cada tempo no cenário
            for idx, duration in enumerate(scenario["all_times"], start=1):
                if idx == 1:
                    status = "warmup"
                elif idx in outlier_indices:
                    status = "outlier"
                else:
                    status = "included"
                writer.writerow([name, idx, f"{duration:.8f}", status, ""])

        # Linha em branco
        writer.writerow([])
        # Cabeçalho para speedups
        writer.writerow(["speedup_scenario", "run_index", "duration", "status", "speedup"])
        # Para cada speedup
        for name, speedup in speedups.items():
            if speedup is None:
                writer.writerow([name, "", "", "speedup", "N/A"])
            else:
                writer.writerow([name, "", "", "speedup", f"{speedup:.8f}"])

# Define uma função para calcular speedups
# Recebe média de A e médias de B
def compute_speedups(a_mean, b_means):
    # Speedup de A em relação a cada versão de B: tempo_B / tempo_A
    if a_mean is None:
        return {name: None for name in b_means}
    return {name: mean / a_mean if mean else None for name, mean in b_means.items()}


# Define a função main
def main():
    # Cria parser para argumentos
    parser = argparse.ArgumentParser(description="Executa benchmark dos programas A e B e salva dados brutos.")
    # Argumento para número de execuções, padrão 30
    parser.add_argument("--runs", type=int, default=30, help="Número de repetições por cenário.")
    # Argumento para prefixo do arquivo de saída
    parser.add_argument("--output", default="benchmark_results", help="Prefixo do arquivo de saída (sem extensão).")
    # Faz parse dos argumentos
    args = parser.parse_args()

    # Obtém o diretório do workspace
    workspace = Path(__file__).resolve().parent
    # Obtém o executável Python
    python_exec = sys.executable

    # Define os cenários de teste
    scenarios = [
        {
            "name": "Programa_A",
            "command": [python_exec, str(workspace / "Programa_A.py")],
        },
        {
            "name": "Programa_B_2_processos",
            "command": [python_exec, str(workspace / "Programa_B.py"), "--workers", "2"],
        },
        {
            "name": "Programa_B_4_processos",
            "command": [python_exec, str(workspace / "Programa_B.py"), "--workers", "4"],
        },
        {
            "name": "Programa_B_8_processos",
            "command": [python_exec, str(workspace / "Programa_B.py"), "--workers", "8"],
        },
    ]

    # Lista para armazenar resultados
    results = []
    # Para cada cenário
    for scenario in scenarios:
        print(f"\nExecutando cenário: {scenario['name']}")
        # Coleta tempos para o cenário
        result = collect_times(scenario["name"], scenario["command"], args.runs)
        # Adiciona aos resultados
        results.append(result)

    # Encontra o resultado de Programa_A
    a_result = next(item for item in results if item["name"] == "Programa_A")
    # Coleta médias de Programa_B
    b_means = {
        item["name"]: item["mean_time"] for item in results if item["name"] != "Programa_A"
    }
    # Calcula speedups
    speedups = compute_speedups(a_result["mean_time"], b_means)

    # Prepara dados de saída
    output_data = {
        "benchmark_runs": args.runs,
        "results": results,
        "speedups": speedups,
    }

    # Define caminhos dos arquivos de saída
    json_path = workspace / f"{args.output}.json"
    csv_path = workspace / f"{args.output}.csv"
    # Salva em JSON
    save_json(output_data, json_path)
    # Salva em CSV
    save_csv(results, speedups, csv_path)

    # Imprime resumo
    print(f"\nBenchmark finalizado.")
    print(f"Arquivo JSON: {json_path}")
    print(f"Arquivo CSV: {csv_path}")
    print("\nSpeedups de Programa_A em relação às versões de Programa_B:")
    for name, speedup in speedups.items():
        if speedup is None:
            print(f"  {name}: não calculado")
        else:
            print(f"  {name}: {speedup:.4f}x")


# Executa a função main se o script for executado diretamente
if __name__ == "__main__":
    main()
