# Importa o módulo hashlib, que fornece funções para criar hashes criptográficos, como MD5
import hashlib

# Define uma função que busca por força bruta o número que gera o hash MD5 alvo
# Recebe o hash alvo e o limite máximo de números a testar
def encontrar_numero_por_hash(hash_alvo, entrada_max):
    # Loop de 1 até entrada_max (inclusive)
    for i in range(1, entrada_max + 1):
        # Converte o número i para string e depois para bytes (necessário para hashlib)
        candidato = str(i).encode()
        # Calcula o hash MD5 do candidato
        hash_gerado = hashlib.md5(candidato).hexdigest()

        # Verifica se o hash gerado é igual ao hash alvo
        if hash_gerado == hash_alvo:
            # Se encontrou, retorna o número i
            return i
    # Se não encontrou nenhum, retorna None
    return None

# Define constantes para o hash alvo e o limite de busca
# Estes são exemplos de hashes MD5 que correspondem a números específicos
ALVO = "d1ca3aaf52b41acd68ebb3bf69079bd1"  # Corresponde ao número "10000000"
ALVO = "283f42764da6dba2522412916b031080"  # Corresponde ao número "9999999"
ALVO = "f0898af949a373e72a4f6a34b4de9090"  # Corresponde ao número "7654321"

# Define o limite máximo de números a testar (10 milhões)
LIMITE = 10000000

# Chama a função para encontrar o número correspondente ao hash alvo dentro do limite
resultado = encontrar_numero_por_hash(ALVO, LIMITE)
# Imprime o resultado (o número encontrado ou None se não encontrou)
print(resultado)