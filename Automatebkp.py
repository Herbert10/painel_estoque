import requests
import jwt

# Configurações do SharePoint
sharepoint_site_url = 'https://alfadashcombr.sharepoint.com/sites/clientes'
sharepoint_list_name = 'clientes'
tenant_id = '9f0d46d9-e274-48ea-956f-d6dc19e1e581'
client_id = '96f8afca-1b24-4615-8535-672e82d3be18'
client_secret = '/rgs/p3a/uHXVIn33peZ7as1PjR1epMJHqipUv/1oU0='

# Função para obter o token de autenticação
def get_sharepoint_token(tenant_id, client_id, client_secret):
    url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://alfadashcombr.sharepoint.com/.default'
    }
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json().get('access_token')

# Função para decodificar o token e verificar permissões
def decode_token(token):
    decoded = jwt.decode(token, options={"verify_signature": False})
    print(decoded)

# Função para obter o tipo de item
def get_item_type(token):
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json;odata=verbose'
    }
    url = f"{sharepoint_site_url}/_api/web/lists/getbytitle('{sharepoint_list_name}')/listItemEntityTypeFullName"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['d']['listItemEntityTypeFullName']

# Obter e imprimir o tipo de item
try:
    # Obter o token de acesso
    token = get_sharepoint_token(tenant_id, client_id, client_secret)
    print(f"Token de acesso: {token}")

    # Decodificar o token para verificar permissões
    decode_token(token)

    # Obter o tipo de item da lista SharePoint
    item_type = get_item_type(token)
    print(f"Tipo de item: {item_type}")
except Exception as e:
    print(f"Erro: {e}")
