import mysql.connector
import fdb

# Função para verificar a existência de um cliente no Firebird e obter o nome
def obter_cliente_firebird_por_taxvat(taxvat, connection):
    firebird_cursor = connection.cursor()
    firebird_query = """
        SELECT cliente FROM clientes
        WHERE CNPJ = ? OR CGC = ?
    """
    firebird_cursor.execute(firebird_query, (taxvat, taxvat))
    result = firebird_cursor.fetchone()
    firebird_cursor.close()
    return result[0] if result else None

# Conexão com o banco de dados MySQL
mysql_connection = mysql.connector.connect(
    host="98.142.102.10",
    user="megatoon_lojam2",
    password="hPG*r37m1B7k@Q",
    database="megatoon_lojam2"
)

# Consulta ao MySQL para obter o cliente com `entity_id` 164
mysql_cursor = mysql_connection.cursor(dictionary=True)
mysql_query = """
    SELECT ce.entity_id, ce.taxvat
    FROM customer_entity ce
    WHERE ce.entity_id = 164
"""
mysql_cursor.execute(mysql_query)
customer = mysql_cursor.fetchone()

# Fechar a conexão com o MySQL
mysql_cursor.close()
mysql_connection.close()

# Conexão com o banco de dados Firebird
firebird_connection = fdb.connect(
    dsn='milleniumflexmetal.ddns.net:C:\\SYS\\BASE\\Millennium',
    user='SYSDBA',
    password='masterkey'
)

# Verificação e retorno do valor `cliente`
if customer:
    taxvat_value = customer['taxvat']
    print(f"Verificando no Firebird o CPF/CNPJ: {taxvat_value}")

    nome_cliente = obter_cliente_firebird_por_taxvat(taxvat_value, firebird_connection)
    if nome_cliente:
        print(f"Cliente {customer['entity_id']}: Encontrado no Firebird com o nome '{nome_cliente}'")
    else:
        print(f"Cliente {customer['entity_id']}: Não encontrado no Firebird")
else:
    # Se não encontrado no MySQL, ainda procuramos no Firebird
    taxvat_value = "<insira-o-valor-necessario>"
    nome_cliente = obter_cliente_firebird_por_taxvat(taxvat_value, firebird_connection)
    if nome_cliente:
        print(f"Cliente não encontrado no MySQL, mas encontrado no Firebird com o nome '{nome_cliente}'")
    else:
        print("Cliente não encontrado no MySQL nem no Firebird")

# Fechar a conexão com o Firebird
firebird_connection.close()
