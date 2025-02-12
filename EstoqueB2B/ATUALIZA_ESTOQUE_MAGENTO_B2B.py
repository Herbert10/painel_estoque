import fdb
import requests
import json
import os
import threading
from tkinter import Tk, ttk
from dotenv import load_dotenv
from requests_oauthlib import OAuth1

# 🔹 Carregar variáveis do arquivo .env
load_dotenv()

# 🔹 Configurações do Firebird
FIREBIRD_DSN = os.getenv("FIREBIRD_DSN")
FIREBIRD_USER = os.getenv("FIREBIRD_USER")
FIREBIRD_PASSWORD = os.getenv("FIREBIRD_PASSWORD")

# 🔹 Configurações do Magento
BASE_URL = os.getenv("MAGENTO_URL", "").strip().replace("https:https://", "https://").rstrip("/")
CONSUMER_KEY = os.getenv("MAGENTO_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("MAGENTO_CONSUMER_SECRET")
ACCESS_TOKEN = os.getenv("MAGENTO_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("MAGENTO_ACCESS_SECRET")

# 🔹 Validação das variáveis de ambiente
if not all([FIREBIRD_DSN, FIREBIRD_USER, FIREBIRD_PASSWORD, BASE_URL, CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN,
            ACCESS_SECRET]):
    raise ValueError(
        "❌ ERRO: Algumas variáveis de ambiente não foram carregadas corretamente. Verifique o arquivo .env.")

print(f"🔍 DEBUG: BASE_URL = {BASE_URL}")

# 🔹 Criar autenticação OAuth1 com HMAC-SHA256
auth = OAuth1(
    CONSUMER_KEY,
    client_secret=CONSUMER_SECRET,
    resource_owner_key=ACCESS_TOKEN,
    resource_owner_secret=ACCESS_SECRET,
    signature_method="HMAC-SHA256"
)


# Função para obter os dados do banco de dados Firebird
def get_stock_data():
    con = fdb.connect(
        dsn=FIREBIRD_DSN,
        user=FIREBIRD_USER,
        password=FIREBIRD_PASSWORD
    )
    cur = con.cursor()
    query = """
    SELECT vps.vitrine_produto_sku AS SKU, 
       SUM(el.saldo) AS QTY 
FROM vitrine_produtos_sku vps
LEFT OUTER JOIN estoques el 
    ON vps.produto = el.produto 
    AND vps.cor = el.cor 
    AND vps.tamanho = el.tamanho
WHERE vps.vitrine = 20107
    AND vps.incluir = 'T'
    AND el.filial IN (2, 14)
    AND el.data_atualizacao >= DATEADD(-1 DAY TO CURRENT_TIMESTAMP)  -- Filtro para os últimos 2 dias
GROUP BY vps.vitrine_produto_sku;
    """
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    con.close()
    return rows


# Função para atualizar o estoque no Magento 2
def update_stock(sku, qty):
    url = f"{BASE_URL}/rest/V1/products/{sku}/stockItems/1"  # 🔄 URL corrigida
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    payload = json.dumps({
        "stock_item": {
            "qty": qty,
            "is_in_stock": qty > 0,
            "manage_stock": True  # 🔄 Corrigido para garantir atualização
        }
    })

    print(f"🔍 DEBUG: Atualizando estoque de {sku} em {url}")
    print(f"🔍 DEBUG: Payload enviado: {payload}")

    try:
        response = requests.put(url, headers=headers, data=payload)
        print(f"🔍 DEBUG: Status Code {response.status_code}, Response: {response.text}")

        if response.status_code == 200:
            print(f"✅ Estoque atualizado para SKU {sku} com {qty} unidades.")
        else:
            print(f"❌ Erro ao atualizar {sku}: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"🚨 ERRO na requisição do SKU {sku}: {e}")


# Interface gráfica
root = Tk()
root.title("Atualização de Estoque")
progresso = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
progresso.pack(pady=10)
label_progresso = ttk.Label(root, text="Processado: 0")
label_progresso.pack(pady=10)
label_rodape = ttk.Label(root, text="Desenvolvido por: Alfa Dash Consultoria e Treinamento Ltda",
                         font=("Helvetica", 10))
label_rodape.pack(side="bottom", pady=10)

cancelar = False


def cancelar_processamento():
    global cancelar
    cancelar = True
    root.destroy()


button_cancelar = ttk.Button(root, text="Cancelar", command=cancelar_processamento)
button_cancelar.pack(pady=10)


# Função para iniciar o processamento
def iniciar_processamento():
    global cancelar
    try:
        stock_data = get_stock_data()

        total_registros = len(stock_data)
        progresso["maximum"] = total_registros

        for i, (sku, qty) in enumerate(stock_data):
            if cancelar:
                break
            update_stock(sku, qty)
            progresso["value"] = i + 1
            label_progresso.config(text=f"Processado: {i + 1} de {total_registros}")
            root.update_idletasks()

    except Exception as e:
        print(f"❌ Erro durante o processamento: {e}")
    finally:
        root.after(0, root.destroy)  # 🔄 Corrigido para evitar erro de thread


# Iniciar o processamento em uma thread separada
thread = threading.Thread(target=iniciar_processamento)
thread.start()
root.mainloop()
