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
import threading
import time
import tkinter as tk
from tkinter import ttk

def conectar_mysql():
    return pymysql.connect(
        host="186.227.196.66",
        user="megatoon_lojam247",
        password="hPG*r37m1B7k@Q",
        database="megatoon_lojam247",
        cursorclass=DictCursor,  # Garante que os resultados sejam retornados como dicionários
        connect_timeout=15
    )

def conectar_postgres():
    return psycopg2.connect(
        host="localhost",
        user="postgres",
        password="Alfa@2024",
        database="Producao"
    )

def enviar_mensagem_whatsapp(numero_pedido, mensagem):
    """Envia mensagem via WhatsApp usando Z-API."""
    url = "https://api.z-api.io/instances/3D0410602BEFB06E5DF6EEE17BD0D626/token/CC6CF6CE09DC42573B89209B/send-text"
    client_token = "F431d58e253c34be3844b4bc62bb831e6S"  # Substitua pelo Client-Token fornecido

    headers = {
        "Content-Type": "application/json",
        "Client-Token": client_token  # Adiciona o Client-Token no header
    }

    if not mensagem or mensagem.strip() == "":
        print(f"Mensagem vazia para o pedido {numero_pedido}. Não foi enviada.")
        return

    payload = {
        "phone": "5511941445959",  # Substitua pelo número de WhatsApp (formato internacional)
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


def atualizar_status_pedido_mysql(numero_pedido):
    """Atualiza o status do pedido no MySQL."""
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
        print(f"Erro ao atualizar o status do pedido {numero_pedido}: {e}")

def buscar_pedidos_em_aberto():
    """Busca pedidos com status 'Pending' no MySQL."""
    query = """
    SELECT so.created_at, so.entity_id, so.increment_id, so.status, so.base_grand_total, 
           so.total_qty_ordered, so.customer_id, so.customer_firstname, so.customer_taxvat
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

def buscar_itens_vendidos():
    """Busca os itens vendidos dos pedidos pendentes."""
    query = """
    SELECT soi.order_id, soi.product_id, soi.sku, soi.qty_ordered, soi.price, soi.row_total
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

def buscar_dados_postgres():
    """Busca informações de produtos no PostgreSQL."""
    query = """
    SELECT vitrine, vitrine_produto_sku, produto, cor, estampa, tamanho, id_externo, colecao
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

def buscar_clientes_postgres():
    """Busca informações de clientes no PostgreSQL."""
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

def decimal_para_float(data):
    """Converte todos os Decimals em um dicionário para float."""
    if isinstance(data, list):
        return [decimal_para_float(item) for item in data]
    elif isinstance(data, dict):
        return {key: decimal_para_float(value) for key, value in data.items()}
    elif isinstance(data, Decimal):
        return float(data)
    else:
        return data


def gerar_json(pedido, itens, produtos, clientes):
    """Gera o JSON para cada pedido."""
    numero_pedido = pedido["increment_id"]
    cliente_id = pedido["customer_id"]

    # Buscar cliente na tabela de clientes
    cliente = next((c["cliente"] for c in clientes if c["entity_id"] == cliente_id), None)
    if not cliente:
        cliente = "Cliente não encontrado"  # Valor padrão caso o cliente não seja encontrado

    # Separar produtos por coleção
    produtos_pedido = [item for item in itens if item["order_id"] == pedido["entity_id"]]
    produtos_por_colecao = {"9": [], "outros": []}

    for produto_pedido in produtos_pedido:
        produto_info = next((p for p in produtos if p["vitrine_produto_sku"] == produto_pedido["sku"]), None)
        if produto_info:
            detalhe = {
                "produto": produto_info["produto"],
                "cor": produto_info["cor"],
                "estampa": produto_info["estampa"],
                "tamanho": produto_info["tamanho"],
                "quantidade": produto_pedido["qty_ordered"],
                "preco": produto_pedido["price"]
            }
            # Verificar coleção e organizar produtos
            if produto_info["colecao"] == 9:
                produtos_por_colecao["9"].append(detalhe)
            else:
                produtos_por_colecao["outros"].append(detalhe)

    pedidos_json = []

    # Criar pedidos para coleção 9
    if produtos_por_colecao["9"]:
        total = sum(item["quantidade"] * item["preco"] for item in produtos_por_colecao["9"])
        quantidade = sum(item["quantidade"] for item in produtos_por_colecao["9"])
        pedidos_json.append({
            "cod_pedidov": f"MGB2B{numero_pedido}FF",
            "cliente": cliente,
            "n_pedido_cliente": numero_pedido,
            "filial": "14",  # Alterado para 14
            "data_emissao": pedido["created_at"].strftime("%Y-%m-%d"),
            "data_entrega": (pedido["created_at"] + timedelta(days=3)).strftime("%Y-%m-%d"),
            "produtos": produtos_por_colecao["9"],
            "lancamentos": [{
                "tipo_pgto": "8",
                "data_vencimento": "2013-11-14",
                "valor_inicial": f"{total:.2f}".replace('.', ',')  # Formatar total com vírgulas
            }],
            "origem_pedido": "MANUAL",  # Alterado para MANUAL
            "tipo_pedido": "22",
            "tabela": "6",
            "quantidade": quantidade,
            "total": round(total, 2),
            "vendedor": 14,  # Alterado para 14
            "transportadora": 553,
            "condicoes_pgto": 8307
        })

    # Criar pedidos para outras coleções
    if produtos_por_colecao["outros"]:
        total = sum(item["quantidade"] * item["preco"] for item in produtos_por_colecao["outros"])
        quantidade = sum(item["quantidade"] for item in produtos_por_colecao["outros"])
        pedidos_json.append({
            "cod_pedidov": f"MGB2B{numero_pedido}FL",
            "cliente": cliente,
            "n_pedido_cliente": numero_pedido,
            "filial": "2",
            "data_emissao": pedido["created_at"].strftime("%Y-%m-%d"),
            "data_entrega": (pedido["created_at"] + timedelta(days=3)).strftime("%Y-%m-%d"),
            "produtos": produtos_por_colecao["outros"],
            "lancamentos": [{
                "tipo_pgto": "8",
                "data_vencimento": "2013-11-14",
                "valor_inicial": f"{total:.2f}".replace('.', ',')  # Formatar total com vírgulas
            }],
            "origem_pedido": "MANUAL",  # Alterado para MANUAL
            "tipo_pedido": "22",
            "tabela": "6",
            "quantidade": quantidade,
            "total": round(total, 2),
            "vendedor": 14,  # Alterado para 14
            "transportadora": 553,
            "condicoes_pgto": 8307
        })

    return decimal_para_float(pedidos_json)


def enviar_para_api(json_data):
    url = "http://milleniumflexmetal.ddns.net:6017/api/millenium/Pedido_venda.inclui"
    usuario = "Administrator"
    senha = "#5252!Mega2019Servidor$"
    headers = {"Content-Type": "application/json"}
    numero_pedido = json_data.get("cod_pedidov", "N/A")
    # Log do JSON enviado
    print("JSON enviado:", json.dumps(json_data, indent=4, ensure_ascii=False))
    try:
        response = requests.post(url, auth=HTTPBasicAuth(usuario, senha), headers=headers, json=json_data)

        if response.status_code == 201:
            mensagem = f"Pedido {numero_pedido} criado com sucesso no sistema."
            print(mensagem)
            enviar_mensagem_whatsapp(numero_pedido, mensagem)
            atualizar_status_pedido_mysql(numero_pedido)
            return "Criado com sucesso"
        elif response.status_code == 200:
            mensagem = f"Pedido {numero_pedido} importado com sucesso no sistema."
            print(mensagem)
            enviar_mensagem_whatsapp(numero_pedido, mensagem)
            atualizar_status_pedido_mysql(numero_pedido)
            return "Importado com sucesso"
        else:
            erro = f"Erro: {response.status_code}, Resposta: {response.text}"
            print(erro)
            enviar_mensagem_whatsapp(numero_pedido, f"Erro ao importar pedido {numero_pedido}: {erro}")
            return erro
    except Exception as e:
        erro = f"Erro de conexão ou processamento: {str(e)}"
        print("Erro detalhado:", erro)
        enviar_mensagem_whatsapp(numero_pedido, f"Erro ao importar pedido {numero_pedido}: {erro}")
        return erro
def processar_pedidos(interface_callback):
    pedidos = buscar_pedidos_em_aberto()
    itens = buscar_itens_vendidos()
    produtos = buscar_dados_postgres()
    clientes = buscar_clientes_postgres()

    for pedido in pedidos:
        pedidos_json = gerar_json(pedido, itens, produtos, clientes)
        for pedido_json in pedidos_json:
            status = enviar_para_api(pedido_json)
            interface_callback(pedido_json["cod_pedidov"], status)

def iniciar_monitoramento(interface_callback):
    while True:
        processar_pedidos(interface_callback)
        time.sleep(30)

# Interface gráfica com tkinter
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitoramento de Pedidos")
        self.tree = ttk.Treeview(root, columns=("Numero Pedido", "Status"), show="headings")
        self.tree.heading("Numero Pedido", text="Número do Pedido")
        self.tree.heading("Status", text="Status")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.data = []

    def atualizar_interface(self, numero_pedido, status):
        self.data.append((numero_pedido, status))
        self.tree.insert("", "end", values=(numero_pedido, status))

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)

    # Iniciar a rotina de monitoramento em uma thread separada
    thread = threading.Thread(target=iniciar_monitoramento, args=(app.atualizar_interface,))
    thread.daemon = True
    thread.start()

    root.mainloop()
