import os
import json
import pymysql
import psycopg2
from psycopg2.extras import RealDictCursor
from pymysql.cursors import DictCursor
from dotenv import load_dotenv
from decimal import Decimal

load_dotenv()

def conectar_mysql():
    """Conecta ao MySQL e retorna a conexão."""
    host = os.getenv("MYSQL_HOST")
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")
    database = os.getenv("MYSQL_DATABASE")
    port = os.getenv("MYSQL_PORT", "3306")

    if not all([host, user, password, database, port]):
        print("❌ Erro: Credenciais do MySQL não foram carregadas corretamente do .env.")
        return None

    try:
        conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=int(port),
            cursorclass=DictCursor,
            connect_timeout=15
        )
        print("✅ Conectado ao MySQL com sucesso!")
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar ao MySQL: {e}")
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


def salvar_json(pedidos_json, numero_pedido):
    """Salva o JSON na pasta C:/DADOS/ com o número do pedido como nome."""
    pasta = r"C:/DADOS"
    if not os.path.exists(pasta):
        os.makedirs(pasta)

    caminho_arquivo = os.path.join(pasta, f"{numero_pedido}.json")

    with open(caminho_arquivo, "w", encoding="utf-8") as arquivo:
        json.dump(pedidos_json, arquivo, indent=4, ensure_ascii=False)

    print(f"✅ JSON salvo em: {caminho_arquivo}")


def gerar_json(pedido, itens, produtos):
    """Gera JSON do pedido e salva no arquivo."""
    numero_pedido = pedido["increment_id"]

    # Separação dos produtos por coleção
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

    pedidos_json = []

    if produtos_filial_14:
        pedidos_json.append({
            "cod_pedidov": f"MGB2B{numero_pedido}FF",
            "filial": "14",
            "data_emissao": pedido["created_at"].strftime("%Y-%m-%d"),
            "produtos": produtos_filial_14
        })

    if produtos_filial_2:
        pedidos_json.append({
            "cod_pedidov": f"MGB2B{numero_pedido}FL",
            "filial": "2",
            "data_emissao": pedido["created_at"].strftime("%Y-%m-%d"),
            "produtos": produtos_filial_2
        })

    salvar_json(pedidos_json, numero_pedido)
    return pedidos_json


def processar_pedidos():
    """Processa todos os pedidos pendentes."""
    print("🔄 Iniciando processamento de pedidos...")

    pedidos = buscar_pedidos_em_aberto()
    if not pedidos:
        print("🔹 Nenhum pedido pendente encontrado.")
        return

    itens = buscar_itens_pedido()
    produtos = buscar_dados_postgres()

    for pedido in pedidos:
        print(f"📦 Processando pedido {pedido['increment_id']}...")
        pedidos_json = gerar_json(pedido, itens, produtos)


if __name__ == "__main__":
    processar_pedidos()
