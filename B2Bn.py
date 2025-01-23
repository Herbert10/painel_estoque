import fdb
import mysql.connector
import logging

# Configuração do logging
logging.basicConfig(filename='process.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    logging.info('Iniciando conexão com o banco de dados Firebird.')
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
    logging.info(f'Consulta ao Firebird executada, {len(results)} produtos encontrados.')

    # Fechar conexão Firebird
    cur_firebird.close()
    conn_firebird.close()
    logging.info('Conexão com o Firebird fechada.')

    logging.info('Iniciando conexão com o banco de dados MySQL.')
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
        conn_mysql.commit()  # Commit após cada update
        logging.info(f'Produto SKU {sku} atualizado com sucesso.')

    # Fechar conexão MySQL
    cur_mysql.close()
    conn_mysql.close()
    logging.info('Conexão com o MySQL fechada e script concluído com sucesso.')

except Exception as e:
    logging.error(f'Erro durante a execução do script: {e}')
    # Aqui você poderia implementar uma notificação de falha, se necessário
finally:
    # Fechar conexões e cursores caso ainda estejam abertos
    if not conn_firebird.closed:
        if not cur_firebird.closed:
            cur_firebird.close()
        conn_firebird.close()
    if not conn_mysql.is_connected():
        if not cur_mysql.closed:
            cur_mysql.close()
        conn_mysql.close()
    logging.info('Script concluído com todas as conexões fechadas.')
