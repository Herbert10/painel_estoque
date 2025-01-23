import fdb
import requests
from requests_oauthlib import OAuth1
import json
from tkinter import Tk, ttk, messagebox
import threading
import sys

# Função para obter os dados do banco de dados Firebird
def get_stock_data():
    con = fdb.connect(
        dsn='milleniumflexmetal.ddns.net:c:/SYS/base/millennium',
        user='SYSDBA',
        password='masterkey'
    )

    cur = con.cursor()
    query = """
    select vps.vitrine_produto_sku as SKU, sum(el.saldo) as QTY 
    from vitrine_produtos_sku vps
    LEFT OUTER join estoques el 
    on (vps.produto=el.produto and vps.cor=el.cor and vps.tamanho=el.tamanho)
    where vps.vitrine = 20107
    and vps.incluir = 'T'
    and el.filial in (2, 14)
    group BY vps.vitrine_produto_sku
    """
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    con.close()
    return rows

# Função para atualizar o estoque no Magento 2
def update_stock(base_url, consumer_key, consumer_secret, token_key, token_secret, sku, qty):
    url = f"{base_url}/rest/V1/products/{sku}/stockItems/1"
    auth = OAuth1(consumer_key, consumer_secret, token_key, token_secret)
    headers = {
        "Content-Type": "application/json"
    }
    payload = json.dumps({
        "stockItem": {
            "qty": qty,
            "is_in_stock": qty > 0
        }
    })
    response = requests.put(url, headers=headers, auth=auth, data=payload)
    return response.json()

# Informações do Magento 2
base_url = "https://megatoon.org/"  # Substitua pela URL base do seu Magento 2
consumer_key = "weup4t3lk3i9084nbcx5sgem3d31bvqi"          # Substitua pela sua Chave do Consumidor
consumer_secret = "2tgot2ylzlgcwrteq5dw89iq58qk8wql"    # Substitua pelo seu Segredo do Consumidor
token_key = "xg8rccrdyjl7j4oidza6byjj5x6hbukk"             # Substitua pelo Token de Acesso
token_secret = "acsret8ahnvw0shikgfkv8k3mny2eur1"   # Substitua pelo Segredo do Token de Acesso

# Configurar a janela de progresso
root = Tk()
root.title("Atualização de Estoque")
progresso = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
progresso.pack(pady=10)
label_progresso = ttk.Label(root, text="Processado: 0")
label_progresso.pack(pady=10)
label_rodape = ttk.Label(root, text="Desenvolvido por: Alfa Dash Consultoria e Treinamento Ltda", font=("Helvetica", 10))
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
        # Obter os dados de estoque do banco de dados Firebird
        stock_data = get_stock_data()

        total_registros = len(stock_data)
        progresso["maximum"] = total_registros

        # Atualizar o estoque no Magento 2 para cada produto em chunks de 20
        for i in range(0, total_registros, 20):
            if cancelar:
                break
            chunk = stock_data[i:i+20]
            for j, row in enumerate(chunk):
                sku = row[0]
                qty = row[1]
                result = update_stock(base_url, consumer_key, consumer_secret, token_key, token_secret, sku, qty)
                print(f"Updated {sku} with quantity {qty}: {result}")

                progresso["value"] = i + j + 1
                label_progresso.config(text=f"Processado: {i + j + 1} de {total_registros}")
                root.update_idletasks()

    except Exception as e:
        print(f"Erro durante o processamento: {e}")
    finally:
        root.destroy()

# Iniciar o processamento em uma thread separada
thread = threading.Thread(target=iniciar_processamento)
thread.start()
root.mainloop()
