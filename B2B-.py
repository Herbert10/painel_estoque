import fdb
import mysql.connector

# Conexão com o Firebird
conn_firebird = fdb.connect(
    host='milleniumflexmetal.ddns.net',
    database='c:\\sys\\base\\millennium',
    user='SYSDBA',
    password='masterkey',
    charset='UTF8'
)
cur_firebird = conn_firebird.cursor()

# Consulta atualizada para retornar todos os produtos
firebird_query = """
SELECT vps.vitrine_produto_sku AS SKU, SUM(el.saldo) AS QTY
FROM vitrine_produtos_sku vps
LEFT OUTER JOIN estoques el ON (vps.produto = el.produto AND vps.cor = el.cor AND vps.tamanho = el.tamanho)
WHERE vps.vitrine = 20107 AND vps.incluir = 'T' AND el.filial IN (2,14)
GROUP BY VPS.vitrine_produto_sku
"""

cur_firebird.execute(firebird_query)
results = cur_firebird.fetchall()

# Fechar conexão Firebird
cur_firebird.close()
conn_firebird.close()

# Conexão com o MySQL
conn_mysql = mysql.connector.connect(
    host='98.142.102.10',
    database='megatoon_lojam2',
    user='megatoon_lojam2',
    password='hPG*r37m1B7k@Q'
)
cur_mysql = conn_mysql.cursor()

# Preparar e executar o update para cada produto
for sku, qty in results:
    is_in_stock = 1 if qty > 0 else 0
    mysql_update_query = """
    UPDATE cataloginventory_stock_item csi
    JOIN catalog_product_entity cpe ON csi.product_id = cpe.entity_id
    SET csi.qty = %s, csi.is_in_stock = %s
    WHERE cpe.sku = %s
    """
    cur_mysql.execute(mysql_update_query, (qty, is_in_stock, sku))

# Commit das mudanças e fechar conexão MySQL
conn_mysql.commit()
cur_mysql.close()
conn_mysql.close()
