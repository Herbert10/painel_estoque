import os
import json
import requests
from requests.auth import HTTPBasicAuth
import pymysql
from pymysql.cursors import DictCursor
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from decimal import Decimal
import time
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

# Configuração do MySQL
def conectar_mysql():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
        cursorclass=DictCursor,
        connect_timeout=15
    )

# Configuração do PostgreSQL
def conectar_postgres():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DATABASE")
    )



# Enviar mensagem via WhatsApp (Z-API)
def enviar_mensagem_whatsapp(numero_pedido, mensagem):
    """Envia mensagem via WhatsApp usando Z-API."""
    url = f"https://api.z-api.io/instances/{os.getenv('ZAPI_INSTANCE')}/token/{os.getenv('ZAPI_TOKEN')}/send-text"

    headers = {
        "Content-Type": "application/json",
        "Client-Token": os.getenv("ZAPI_CLIENT_TOKEN")
    }

    payload = {
        "phone": os.getenv("ZAPI_PHONE"),
        "message": mensagem
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"Mensagem enviada com sucesso: Pedido {numero_pedido}")
        else:
            print(f"Erro ao enviar mensagem via Z-API: {response.text}")
    except Exception as e:
        print(f"Erro na integração com Z-API: {e}")

# Atualizar status do pedido no MySQL após envio
def atualizar_status_pedido_mysql(numero_pedido):
    query = """
    UPDATE sales_order
    SET state = 'processing', status = 'processing'
    WHERE increment_id = %s
    """
    try:
        with conectar_mysql() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (numero_pedido,))
                conn.commit()
                print(f"Pedido {numero_pedido} atualizado para 'processing'")
    except Exception as e:
        print(f"Erro ao atualizar status do pedido {numero_pedido}: {e}")

# Buscar pedidos pendentes no MySQL
def buscar_pedidos_em_aberto():
    query = """
    SELECT so.created_at, so.entity_id, so.increment_id, so.status, 
           so.base_grand_total, so.total_qty_ordered, so.customer_id
    FROM sales_order so
    WHERE so.status = 'Pending'
    """
    try:
        with conectar_mysql() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchall()
    except Exception as e:
        print(f"Erro ao buscar pedidos pendentes: {e}")
        return []

# Buscar itens vendidos no MySQL
def buscar_itens_vendidos():
    query = """
    SELECT soi.order_id, soi.product_id, soi.sku, soi.qty_ordered, soi.price
    FROM sales_order_item soi
    LEFT JOIN sales_order so ON soi.order_id = so.entity_id
    WHERE so.status = 'Pending'
    """
    try:
        with conectar_mysql() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchall()
    except Exception as e:
        print(f"Erro ao buscar itens vendidos: {e}")
        return []

# Buscar produtos do PostgreSQL
def buscar_dados_postgres():
    query = """
    SELECT vitrine_produto_sku, produto, cor, estampa, tamanho, colecao
    FROM megatoon.produtos_vitrine_sku
    """
    try:
        with conectar_postgres() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query)
                return cursor.fetchall()
    except Exception as e:
        print(f"Erro ao buscar dados de produtos: {e}")
        return []

# Buscar clientes do PostgreSQL
def buscar_clientes_postgres():
    query = """
    SELECT cliente, entity_id 
    FROM megatoon.nova_tabela_clientes_integração
    """
    try:
        with conectar_postgres() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query)
                return cursor.fetchall()
    except Exception as e:
        print(f"Erro ao buscar dados de clientes: {e}")
        return []

# Enviar pedido para a API do sistema
def enviar_para_api(json_data):
    url = os.getenv("API_MILLENIUM_URL")

    response = requests.post(url, auth=HTTPBasicAuth(os.getenv("API_MILLENIUM_USER"), os.getenv("API_MILLENIUM_PASSWORD")), json=json_data)

    if response.status_code == 201:
        print(f"Pedido {json_data['cod_pedidov']} criado com sucesso.")
        atualizar_status_pedido_mysql(json_data['cod_pedidov'])
    else:
        print(f"Erro ao criar pedido: {response.text}")
        enviar_mensagem_whatsapp(json_data['cod_pedidov'], f"Erro ao criar pedido: {response.text}")

# Processar pedidos
def processar_pedidos():
    pedidos = buscar_pedidos_em_aberto()
    itens = buscar_itens_vendidos()
    produtos = buscar_dados_postgres()
    clientes = buscar_clientes_postgres()

    for pedido in pedidos:
        pedidos_json = gerar_json(pedido, itens, produtos, clientes)
        for pedido_json in pedidos_json:
            enviar_para_api(pedido_json)

# Loop de monitoramento a cada 30 segundos
while True:
    processar_pedidos()
    time.sleep(30)
