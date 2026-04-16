# Importa o módulo argparse para lidar com argumentos da linha de comando
import argparse
# Importa concurrent.futures para executar tarefas em paralelo usando processos
import concurrent.futures
# Importa hashlib para calcular hashes MD5
import hashlib

# Define uma função que busca o número correspondente ao hash dentro de um intervalo específico
# Recebe o hash alvo, o início e o fim do intervalo
def encontrar_numero_por_hash(hash_alvo, inicio, fim):
    # Loop do início até o fim (inclusive)
    for i in range(inicio, fim + 1):
        # Verifica se o hash MD5 de str(i) é igual ao hash alvo
        if hashlib.md5(str(i).encode()).hexdigest() == hash_alvo:
            # Se encontrou, retorna o número i
            return i
    # Se não encontrou, retorna None
    return None

# Define uma função para dividir o espaço de busca em intervalos para os workers
# Recebe o limite total e o número de workers
def gerar_intervalos(limite, workers):
    # Calcula o tamanho aproximado de cada intervalo
    tamanho = limite // workers
    # Inicializa uma lista para armazenar os intervalos
    intervalos = []
    # Define o início do primeiro intervalo
    inicio = 1

    # Loop para cada worker
    for i in range(workers):
        # Calcula o fim do intervalo atual
        fim = inicio + tamanho - 1
        # Para o último worker, ajusta o fim para o limite total
        if i == workers - 1:
            fim = limite
        # Adiciona o intervalo (inicio, fim) à lista
        intervalos.append((inicio, fim))
        # Atualiza o início para o próximo intervalo
        inicio = fim + 1

    # Retorna a lista de intervalos
    return intervalos

# Define a função principal para busca paralela usando multiprocessing
# Recebe o hash alvo, o limite e o número de workers
def buscar_paralelo(hash_alvo, limite, workers):
    # Gera os intervalos para os workers
    intervalos = gerar_intervalos(limite, workers)

    # Cria um ProcessPoolExecutor com o número de workers especificado
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        # Submete tarefas para cada intervalo, chamando encontrar_numero_por_hash
        futures = [executor.submit(encontrar_numero_por_hash, hash_alvo, inicio, fim)
                   for inicio, fim in intervalos]

        # Aguarda as tarefas completarem e verifica os resultados
        for future in concurrent.futures.as_completed(futures):
            # Obtém o resultado da tarefa
            resultado = future.result()
            # Se encontrou um resultado (não None), retorna imediatamente
            if resultado is not None:
                return resultado

    # Se nenhum worker encontrou, retorna None
    return None

# Define a função main para configurar e executar o programa
def main():
    # Cria um parser para argumentos da linha de comando
    parser = argparse.ArgumentParser(description="Busca paralela de hash MD5 com número de workers configurável.")
    # Adiciona argumento para o hash alvo, com valor padrão
    parser.add_argument("--hash", default="f0898af949a373e72a4f6a34b4de9090",
                        help="Hash MD5 alvo para encontrar o número correspondente.")
    # Adiciona argumento para o limite, com valor padrão e tipo int
    parser.add_argument("--limit", type=int, default=10000000,
                        help="Máximo número a testar.")
    # Adiciona argumento para o número de workers, com valor padrão e tipo int
    parser.add_argument("--workers", type=int, default=12,
                        help="Número de processos a usar.")
    # Faz o parse dos argumentos
    args = parser.parse_args()

    # Chama a função de busca paralela com os argumentos fornecidos
    resultado = buscar_paralelo(args.hash, args.limit, args.workers)
    # Imprime o resultado
    print(resultado)


if __name__ == "__main__":
    main()