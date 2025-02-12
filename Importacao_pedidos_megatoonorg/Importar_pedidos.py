import os
import json
import requests
import pymysql
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from pymysql.cursors import DictCursor
from dotenv import load_dotenv
from decimal import Decimal
from datetime import datetime, timedelta

# Carregar variáveis do arquivo .env
load_dotenv()

# Carregar variáveis do .env
ZAPI_URL_BASE = os.getenv("ZAPI_URL_BASE")
ZAPI_CLIENT_TOKEN = os.getenv("ZAPI_CLIENT_TOKEN")
WHATSAPP_NUMEROS = os.getenv("WHATSAPP_NUMEROS", "").split(",")
API_URL = os.getenv("API_URL")
API_USER = os.getenv("API_USER")
API_PASSWORD = os.getenv("API_PASSWORD")

def conectar_mysql():
    """Conecta ao MySQL e retorna a conexão."""
    try:
        conn = pymysql.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE"),
            port=int(os.getenv("MYSQL_PORT", 3306)),
            cursorclass=DictCursor,
            connect_timeout=15
        )
        print("✅ Conectado ao MySQL com sucesso!")
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar ao MySQL: {e}")
        return None

def conectar_postgres():
    """Conecta ao PostgreSQL e retorna a conexão."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            database=os.getenv("POSTGRES_DATABASE"),
            port=int(os.getenv("POSTGRES_PORT", 5432)),
            options="-c client_encoding=UTF8"
        )
        print("✅ Conectado ao PostgreSQL com sucesso!")
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar ao PostgreSQL: {e}")
        return None

def buscar_pedidos_em_aberto():
    """Busca pedidos pendentes no MySQL."""
    query = """
    SELECT so.created_at, so.entity_id, so.increment_id, so.status, so.base_grand_total, 
           so.total_qty_ordered, so.customer_id, so.customer_firstname, so.customer_taxvat
    FROM sales_order so
    WHERE so.status = 'Pending'
    """
    conn = conectar_mysql()
    if not conn:
        return []

    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            pedidos = cursor.fetchall()
            print(f"🔹 {len(pedidos)} pedidos pendentes encontrados.")
            return pedidos
    except Exception as e:
        print(f"❌ Erro ao buscar pedidos no MySQL: {e}")
        return []
    finally:
        conn.close()

def buscar_itens_pedido():
    """Busca os itens vendidos dos pedidos pendentes no MySQL."""
    query = """
    SELECT soi.order_id, soi.product_id, soi.sku, soi.qty_ordered, soi.price, soi.row_total
    FROM sales_order_item soi
    LEFT JOIN sales_order so ON soi.order_id = so.entity_id
    WHERE so.status = 'Pending'
    """
    conn = conectar_mysql()
    if not conn:
        return []

    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()
    except Exception as e:
        print(f"❌ Erro ao buscar itens do pedido: {e}")
        return []
    finally:
        conn.close()

def buscar_dados_postgres():
    """Busca informações de produtos no PostgreSQL."""
    query = """
    SELECT vitrine_produto_sku, produto, cor, estampa, tamanho, colecao
    FROM megatoon.produtos_vitrine_sku
    """
    conn = conectar_postgres()
    if not conn:
        return []

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            return cursor.fetchall()
    except Exception as e:
        print(f"❌ Erro ao buscar dados de produtos: {e}")
        return []
    finally:
        conn.close()

def buscar_cliente_postgres(customer_taxvat):
    """Busca o cliente no PostgreSQL baseado no CPF/CNPJ."""
    query = """
    SELECT cliente
    FROM megatoon."clientes_integração"
    WHERE cnpj = %s OR cgc = %s OR cpf = %s
    LIMIT 1
    """
    conn = conectar_postgres()
    if not conn:
        return None

    try:
        with conn.cursor() as cursor:
            cursor.execute(query, (customer_taxvat, customer_taxvat, customer_taxvat))
            resultado = cursor.fetchone()
            return resultado[0] if resultado else None
    except Exception as e:
        print(f"❌ Erro ao buscar cliente no PostgreSQL: {e}")
        return None
    finally:
        conn.close()

def decimal_para_float(dados):
    """Converte todos os valores Decimal para float em um dicionário ou lista."""
    if isinstance(dados, list):
        return [decimal_para_float(item) for item in dados]
    elif isinstance(dados, dict):
        return {key: decimal_para_float(value) for key, value in dados.items()}
    elif isinstance(dados, Decimal):
        return float(dados)
    else:
        return dados


def enviar_pedido_api(pedido_json, entity_id):
    """Envia o pedido para a API e verifica se já foi enviado."""

    print(f"🚀 Tentando enviar pedido: {pedido_json['cod_pedidov']} para a API...")

    if not API_URL or not API_USER or not API_PASSWORD:
        print("❌ Erro: Credenciais da API não configuradas corretamente no .env.")
        return

    try:
        response = requests.post(
            API_URL,
            auth=(API_USER, API_PASSWORD),
            json=pedido_json,
            headers={"Content-Type": "application/json"}
        )

        print(f"🔍 Status da resposta: {response.status_code}")
        print(f"📄 Resposta da API: {response.text}")

        if response.status_code == 201:  # Pedido criado com sucesso
            print(f"✅ Pedido {pedido_json['cod_pedidov']} enviado com sucesso!")

            # Atualizar status do pedido para 'processing'
            atualizar_status_pedido(entity_id)

            return True  # Indica que o pedido foi enviado corretamente

        elif response.status_code == 400 and "já existente" in response.text:
            print(f"⚠️ Pedido {pedido_json['cod_pedidov']} já existe na API. Ignorando envio duplicado.")
            return False  # Evita reenviar pedidos duplicados

        else:
            print(f"⚠️ Erro ao enviar pedido {pedido_json['cod_pedidov']}: {response.status_code} - {response.text}")
            return False

    except requests.RequestException as e:
        print(f"❌ Erro ao conectar à API: {e}")
        return False


def enviar_whatsapp(cod_pedidov):
    """Envia uma mensagem para os números cadastrados informando que o pedido foi inserido."""

    # 🔹 Carregar configurações do .env
    ZAPI_INSTANCE_ID = os.getenv("ZAPI_INSTANCE_ID")
    ZAPI_CLIENT_TOKEN = os.getenv("ZAPI_CLIENT_TOKEN")
    CLIENTE_TOKEN = os.getenv("CLIENTE_TOKEN")  # 🔹 Novo token extra
    ZAPI_URL_BASE = os.getenv("ZAPI_URL_BASE")
    WHATSAPP_NUMEROS = os.getenv("WHATSAPP_NUMEROS", "").split(",")

    if not ZAPI_INSTANCE_ID or not ZAPI_CLIENT_TOKEN or not ZAPI_URL_BASE or not CLIENTE_TOKEN:
        print("❌ ERRO: Configuração da Z-API não encontrada no .env")
        return

    # 🔹 Construir a URL correta
    zapi_url = f"{ZAPI_URL_BASE}/{ZAPI_INSTANCE_ID}/token/{ZAPI_CLIENT_TOKEN}/send-text"

    headers = {
        "Content-Type": "application/json",
        "Client-Token": CLIENTE_TOKEN  # 🔹 Adicionando o Client-Token como no Power Automate
    }

    mensagem = (
        f"📦 Pedido nº {cod_pedidov} inserido no Millennium. \r\n"
        "Favor preencher as informações faltantes e/ou repassar para o vendedor responsável. \r\n"
            )

    for numero in WHATSAPP_NUMEROS:
        numero = numero.strip()  # 🔹 Remover espaços extras

        payload = {
            "phone": numero,
            "message": mensagem
        }

        print(f"📤 DEBUG: Enviando payload para {numero}: {json.dumps(payload, indent=2)}")

        try:
            response = requests.post(zapi_url, json=payload, headers=headers)

            print(f"🔍 Status da resposta: {response.status_code}")
            print(f"📄 Resposta da API: {response.text}")

            if response.status_code == 200:
                print(f"✅ Mensagem enviada com sucesso para {numero}!")
            else:
                print(f"⚠️ Falha ao enviar mensagem para {numero}: {response.text}")

        except requests.RequestException as e:
            print(f"❌ Erro ao conectar à Z-API: {e}")
def atualizar_status_pedido(entity_id):
    """Atualiza o status do pedido no MySQL para 'processing' nas tabelas sales_order e sales_order_grid."""
    query_sales_order = """
    UPDATE sales_order 
    SET status = 'processing', state = 'processing'
    WHERE entity_id = %s
    """

    query_sales_order_grid = """
    UPDATE sales_order_grid
    SET status = 'processing'
    WHERE entity_id = %s
    """

    conn = conectar_mysql()
    if not conn:
        return

    try:
        with conn.cursor() as cursor:
            cursor.execute(query_sales_order, (entity_id,))
            cursor.execute(query_sales_order_grid, (entity_id,))
            conn.commit()
            print(f"🔄 Status do pedido {entity_id} atualizado para 'processing' em sales_order e sales_order_grid.")
    except Exception as e:
        print(f"❌ Erro ao atualizar status do pedido {entity_id}: {e}")
    finally:
        conn.close()
def salvar_json(pedido_json, nome_arquivo, entity_id):
    """Salva o JSON na pasta e envia para a API, depois notifica via WhatsApp."""
    pasta = r"C:/DADOS"
    if not os.path.exists(pasta):
        os.makedirs(pasta)

    caminho_arquivo = os.path.join(pasta, f"{nome_arquivo}.json")

    pedido_json = decimal_para_float(pedido_json)

    with open(caminho_arquivo, "w", encoding="utf-8") as arquivo:
        json.dump(pedido_json, arquivo, indent=4, ensure_ascii=False)

    print(f"✅ JSON salvo em: {caminho_arquivo}")

    # Enviar para API e atualizar status do pedido no MySQL
    pedido_enviado = enviar_pedido_api(pedido_json, entity_id)

    if pedido_enviado:
        enviar_whatsapp(pedido_json["cod_pedidov"])  # Enviar mensagem ao WhatsApp

def gerar_json(pedido, itens, produtos):
    """Gera JSONs separados por filial, salva os arquivos e envia para a API."""

    entity_id = pedido["entity_id"]  # Apenas para atualização do status no MySQL
    numero_pedido = pedido["increment_id"]
    customer_taxvat = pedido["customer_taxvat"]

    cliente = buscar_cliente_postgres(customer_taxvat)
    if not cliente:
        print(f"⚠️ Cliente não encontrado para CPF/CNPJ {customer_taxvat}. Pulando pedido {numero_pedido}.")
        return

    data_emissao = pedido["created_at"].strftime("%Y-%m-%d")
    data_entrega = (pedido["created_at"] + timedelta(days=3)).strftime("%Y-%m-%d")

    produtos_filial_14 = []
    produtos_filial_2 = []

    for item in itens:
        if item["order_id"] == pedido["entity_id"]:
            produto_info = next((p for p in produtos if p["vitrine_produto_sku"] == item["sku"]), None)
            if produto_info:
                detalhe = {
                    "produto": produto_info["produto"],
                    "cor": produto_info["cor"],
                    "estampa": produto_info["estampa"],
                    "tamanho": produto_info["tamanho"],
                    "quantidade": item["qty_ordered"],
                    "preco": item["price"]
                }
                if produto_info["colecao"] == 9:
                    produtos_filial_14.append(detalhe)
                else:
                    produtos_filial_2.append(detalhe)

    pedido_enviado = False

    for filial, produtos in [("14", produtos_filial_14), ("2", produtos_filial_2)]:
        if produtos:
            total = sum(item["quantidade"] * item["preco"] for item in produtos)
            quantidade = sum(item["quantidade"] for item in produtos)

            pedido_json = {
                "cod_pedidov": f"MGB2B{numero_pedido}{'FF' if filial == '14' else 'FL'}",
                "cliente": cliente,
                "filial": int(filial),
                "data_emissao": data_emissao,
                "data_entrega": data_entrega,
                "produtos": produtos,
                "total": round(total, 2),
                "quantidade": quantidade,
                "lancamentos": [
                    {
                        "tipo_pgto": "8",
                        "data_vencimento": data_emissao,
                        "valor_inicial": round(total, 2)
                    }
                ],
                "origem_pedido": "WEBSITE",
                "tipo_pedido": "22",
                "tabela": "6",
                "vendedor": 14,
                "transportadora": 553,
                "condicoes_pgto": 8307
            }

            if not pedido_enviado:
                pedido_enviado = salvar_json(pedido_json, pedido_json["cod_pedidov"], entity_id)
            else:
                print(f"🔄 Pedido {pedido_json['cod_pedidov']} não será enviado pois um similar já foi aceito pela API.")

def processar_pedidos():
    """Processa pedidos pendentes a cada 60 segundos."""
    while True:
        print("🔍 Buscando pedidos pendentes...")
        pedidos = buscar_pedidos_em_aberto()
        if pedidos:
            itens = buscar_itens_pedido()
            produtos = buscar_dados_postgres()

            for pedido in pedidos:
                gerar_json(pedido, itens, produtos)
        else:
            print("✅ Nenhum pedido pendente encontrado.")

        print("⏳ Aguardando 60 segundos para nova verificação...")
        time.sleep(60)

if __name__ == "__main__":
    processar_pedidos()
