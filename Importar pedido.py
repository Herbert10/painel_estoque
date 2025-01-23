import requests
import json

# Carregar o JSON do arquivo
file_path = 'C:\\dados\\000003279.json'  # Modifique para o caminho correto do arquivo
with open(file_path, 'r') as file:
    data = json.load(file)

# URL da API
url = 'http://localhost:6017/api/millenium_eco/pedido_venda/inclui'

# Cabeçalhos da requisição, ajuste conforme necessário
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer seu_token_aqui'  # Inclua seu token de autorização, se necessário
}

# Fazer a requisição POST
response = requests.post(url, headers=headers, json=data)

# Verificar a resposta
if response.status_code == 200:
    print("Pedido de venda incluído com sucesso!")
    print(response.json())  # Imprime a resposta da API
else:
    print(f"Erro ao incluir pedido de venda: {response.status_code}")
    print(response.text)  # Imprime a mensagem de erro, se houver
