from suds.client import Client
import fdb
import os
from dotenv import load_dotenv

# 🔹 Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# 🔹 Configuração da API SOAP do Magento 1
MAGENTO_WSDL_URL = os.getenv("MAGENTO_WSDL_URL")
MAGENTO_USER = os.getenv("MAGENTO_API_USER")
MAGENTO_PASSWORD = os.getenv("MAGENTO_API_KEY")

# 🔹 Configuração do Firebird
FIREBIRD_DSN = os.getenv("FIREBIRD_DSN")
FIREBIRD_USER = os.getenv("FIREBIRD_USER")
FIREBIRD_PASSWORD = os.getenv("FIREBIRD_PASSWORD")

# 🔹 Conectar à API SOAP do Magento 1
client = Client(MAGENTO_WSDL_URL)

try:
    session_id = client.service.login(MAGENTO_USER, MAGENTO_PASSWORD)
    print(f"🔍 DEBUG: Sessão Magento iniciada -> {session_id}")
except Exception as e:
    print(f"❌ Erro ao autenticar na API do Magento: {e}")
    exit(1)

# 🔹 Função para obter os dados do banco Firebird
def get_stock_data():
    try:
        con = fdb.connect(
            dsn=FIREBIRD_DSN,
            user=FIREBIRD_USER,
            password=FIREBIRD_PASSWORD
        )
        cur = con.cursor()
        query = """
        SELECT vps.vitrine_produto_sku AS SKU, SUM(el.saldo) AS QTY 
        FROM vitrine_produtos_sku vps
        LEFT OUTER JOIN estoques el 
            ON (vps.produto = el.produto AND vps.cor = el.cor AND vps.tamanho = el.tamanho)
        WHERE vps.vitrine = 20107
            AND vps.incluir = 'T'
            AND el.filial IN (2, 14)
        GROUP BY vps.vitrine_produto_sku;
        """
        cur.execute(query)
        rows = cur.fetchall()
        cur.close()
        con.close()
        return rows
    except Exception as e:
        print(f"❌ Erro ao conectar ao Firebird: {e}")
        return []

# 🔹 Obtém os dados do estoque
stock_data = get_stock_data()

# 🔹 Se não houver produtos, encerra o script
if not stock_data:
    print("❌ Nenhum produto encontrado para atualizar o estoque.")
    client.service.endSession(session_id)
    exit(1)

# 🔹 Montar os arrays para envio em massa
product_ids = []
product_data = []

for sku, qty in stock_data:
    product_ids.append(sku)
    product_data.append({
        "product_id": sku,  # Se necessário, pode ser "sku"
        "qty": qty,
        "is_in_stock": int(qty > 0),
        "manage_stock": 1
    })

# 🔹 Enviar atualização de estoque em massa
try:
    response = client.service.catalogInventoryStockItemMultiUpdate(session_id, product_ids, product_data)
    print(f"✅ Estoque atualizado com sucesso: {response}")
except Exception as e:
    print(f"❌ Erro ao atualizar estoque: {e}")

# 🔹 Finalizar sessão
client.service.endSession(session_id)
print("🔚 Sessão Magento encerrada com sucesso.")
