import argparse
import csv
import json
import subprocess
import sys
import statistics
import time
from pathlib import Path


def run_program(command):
    start = time.perf_counter()
    subprocess.run(command, shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    end = time.perf_counter()
    return end - start


def reject_outliers(times):
    if len(times) < 4:
        return []

    sorted_times = sorted(times)
    q1 = statistics.median(sorted_times[: len(sorted_times) // 2])
    q3 = statistics.median(sorted_times[(len(sorted_times) + 1) // 2 :])
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    return [index for index, t in enumerate(times, start=2) if t < lower or t > upper]


def collect_times(name, command, runs):
    all_times = []
    for i in range(1, runs + 1):
        duration = run_program(command)
        all_times.append(duration)
        print(f"{name} run {i}/{runs}: {duration:.4f}s")

    warmup_excluded = [1]
    candidate_times = all_times[1:]
    outlier_indices = reject_outliers(candidate_times)
    included = [t for idx, t in enumerate(candidate_times, start=2) if idx not in outlier_indices]

    if included:
        mean_time = statistics.mean(included)
    else:
        mean_time = None

    return {
        "name": name,
        "command": command,
        "all_times": all_times,
        "warmup_excluded": warmup_excluded,
        "outlier_excluded": outlier_indices,
        "included_times": included,
        "mean_time": mean_time,
    }


def save_json(results, output_path):
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(results, file, indent=2)


def save_csv(results, output_path):
    with open(output_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["scenario", "run_index", "duration", "status"])
        for scenario in results:
            name = scenario["name"]
            outlier_indices = set(scenario["outlier_excluded"])
            for idx, duration in enumerate(scenario["all_times"], start=1):
                if idx == 1:
                    status = "warmup"
                elif idx in outlier_indices:
                    status = "outlier"
                else:
                    status = "included"
                writer.writerow([name, idx, f"{duration:.8f}", status])


def compute_speedups(a_mean, b_means):
    return {name: a_mean / mean if mean else None for name, mean in b_means.items()}


def main():
    parser = argparse.ArgumentParser(description="Executa benchmark dos programas A e B e salva dados brutos.")
    parser.add_argument("--runs", type=int, default=30, help="Número de repetições por cenário.")
    parser.add_argument("--output", default="benchmark_results", help="Prefixo do arquivo de saída (sem extensão).")
    args = parser.parse_args()

    workspace = Path(__file__).resolve().parent
    python_exec = sys.executable

    scenarios = [
        {
            "name": "Programa_A",
            "command": [python_exec, str(workspace / "Programa_A.py")],
        },
        {
            "name": "Programa_B_2_threads",
            "command": [python_exec, str(workspace / "Programa_B.py"), "--workers", "2", "--mode", "thread"],
        },
        {
            "name": "Programa_B_4_threads",
            "command": [python_exec, str(workspace / "Programa_B.py"), "--workers", "4", "--mode", "thread"],
        },
        {
            "name": "Programa_B_8_threads",
            "command": [python_exec, str(workspace / "Programa_B.py"), "--workers", "8", "--mode", "thread"],
        },
    ]

    results = []
    for scenario in scenarios:
        print(f"\nExecutando cenário: {scenario['name']}")
        result = collect_times(scenario["name"], scenario["command"], args.runs)
        results.append(result)

    a_result = next(item for item in results if item["name"] == "Programa_A")
    b_means = {
        item["name"]: item["mean_time"] for item in results if item["name"] != "Programa_A"
    }
    speedups = compute_speedups(a_result["mean_time"], b_means)

    output_data = {
        "benchmark_runs": args.runs,
        "results": results,
        "speedups": speedups,
    }

    json_path = workspace / f"{args.output}.json"
    csv_path = workspace / f"{args.output}.csv"
    save_json(output_data, json_path)
    save_csv(results, csv_path)

    print(f"\nBenchmark finalizado.")
    print(f"Arquivo JSON: {json_path}")
    print(f"Arquivo CSV: {csv_path}")
    print(f"Speedups: {speedups}")


if __name__ == "__main__":
    main()
