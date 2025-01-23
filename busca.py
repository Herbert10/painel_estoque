import requests
from datetime import datetime, timedelta

# Configurações de autenticação
USERNAME = 'Administrator'
PASSWORD = '#5252!Mega2019Servidor$'


# Função para obter a lista de clientes
def obter_lista_clientes():
    url = 'http://milleniumflexmetal.ddns.net:6017/api/millenium/clientes/lista_clientes'
    try:
        response = requests.get(url, auth=(USERNAME, PASSWORD))
        if response.status_code == 200:
            return response.json()['value']
        else:
            print(f"Erro ao obter lista de clientes: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Erro ao obter lista de clientes: {e}")
        return None


# Função para buscar detalhes de um cliente específico
def buscar_cliente(cliente_id):
    url = f'http://milleniumflexmetal.ddns.net:6017/api/millenium/clientes/busca?cliente={cliente_id}'
    try:
        response = requests.get(url, auth=(USERNAME, PASSWORD))
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erro ao obter detalhes do cliente {cliente_id}: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Erro ao obter detalhes do cliente {cliente_id}: {e}")
        return None


# Função para filtrar clientes com data de atualização ou cadastro entre hoje e os últimos 20 dias
def filtrar_clientes_por_data(clientes):
    clientes_filtrados = []
    data_limite = datetime.now() - timedelta(days=20)

    for cliente in clientes:
        detalhes_cliente = buscar_cliente(cliente['cliente'])
        if detalhes_cliente:
            data_atualizacao = detalhes_cliente.get('data_atualizacao')
            data_cadastro = detalhes_cliente.get('data_cadastro')

            # Converter as datas para objetos datetime
            if data_atualizacao:
                data_atualizacao = datetime.strptime(data_atualizacao, '%Y-%m-%d')
            if data_cadastro:
                data_cadastro = datetime.strptime(data_cadastro, '%Y-%m-%d')

            # Verificar se alguma das datas está dentro do intervalo
            if (data_atualizacao and data_atualizacao >= data_limite) or \
                    (data_cadastro and data_cadastro >= data_limite):
                clientes_filtrados.append(detalhes_cliente)
                print(
                    f"Cliente encontrado: {detalhes_cliente['nome']} - Atualização: {data_atualizacao}, Cadastro: {data_cadastro}")

    return clientes_filtrados


# Execução principal
clientes = obter_lista_clientes()
if clientes:
    clientes_filtrados = filtrar_clientes_por_data(clientes)
    if clientes_filtrados:
        print(f"\nTotal de clientes encontrados: {len(clientes_filtrados)}")
    else:
        print("Nenhum cliente encontrado com atualização ou cadastro nos últimos 20 dias.")
else:
    print("Não foi possível obter a lista de clientes.")
