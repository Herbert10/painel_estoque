import mysql.connector
import json

# Conexão com o MySQL
conn = mysql.connector.connect(
    host='98.142.102.10',
    database='megatoon_lojam2',
    user='megatoon_lojam2',
    password='hPG*r37m1B7k@Q'
)
cursor = conn.cursor(dictionary=True)

# Query MySQL
query = """
SELECT so.increment_id as cod_pedidov, so.created_at as data_emissao, so.created_at as data_entrega,
'0' as acerto, so.discount_amount as v_acerto, so.grand_total , so.total_qty_ordered, soi.qty_ordered,
soi.price, '' as obs_item, soi.sku, 'false' as brindesite, '0', soi.discount_amount as desconto, '0' as cortesia, '0' as v_frete, 
'B2B' as origem_pedido, 20107 as vitrine
FROM sales_order so 
LEFT OUTER JOIN sales_order_item soi ON (so.entity_id = soi.order_id)
WHERE so.increment_id = '000003279'
"""

cursor.execute(query)
results = cursor.fetchall()

# Fechar a conexão
cursor.close()
conn.close()

# Verificar se há resultados antes de processar
if results:
    order_data = {
        "cod_pedidov": results[0]["cod_pedidov"],
        "data_emissao": results[0]["data_emissao"].isoformat(),
        "data_entrega": results[0]["data_entrega"].isoformat(),
        "acerto": int(results[0]["acerto"]),
        "v_acerto": float(results[0]["v_acerto"]),
        "total": float(results[0]["grand_total"]),
        "quantidade": int(results[0]["total_qty_ordered"]),
        "produtos": [],
        "cortesia": int(results[0]["cortesia"]),
        "v_frete": float(results[0]["v_frete"]),
        "origem_pedido": results[0]["origem_pedido"],
        "vitrine": results[0]["vitrine"]
    }

    # Adicionar produtos
    for result in results:
        product = {
            "quantidade": int(result["qty_ordered"]),
            "preco": float(result["price"]),
            "obs_item": result["obs_item"],
            "sku": result["sku"],
            "brindesite": result["brindesite"] == 'true',
            "desconto": float(result["desconto"])
        }
        order_data["produtos"].append(product)

    # Caminho do arquivo JSON a ser salvo
    file_path = f'C:\\dados\\{order_data["cod_pedidov"]}.json'

    # Salvar os dados em um arquivo JSON
    with open(file_path, 'w') as json_file:
        json.dump(order_data, json_file, indent=4)

    print(f"Arquivo JSON gerado com sucesso em {file_path}!")
else:
    print("Nenhum resultado encontrado para o pedido especificado.")
