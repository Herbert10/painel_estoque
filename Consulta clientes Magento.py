import mysql.connector
import fdb

# Função para obter o nome do cliente e o gerador no Firebird com base no taxvat
def obter_cliente_firebird_por_taxvat(taxvat, connection):
    firebird_cursor = connection.cursor()
    firebird_query = """
        SELECT cliente, gerador FROM clientes
        WHERE CNPJ = ? OR CGC = ? OR CPF = ?
    """
    firebird_cursor.execute(firebird_query, (taxvat, taxvat, taxvat))
    result = firebird_cursor.fetchone()
    firebird_cursor.close()
    return result if result else (None, None)

# Função para buscar endereço cadastrado no Firebird com base no gerador
def buscar_endereco_cadastro(gerador, connection):
    firebird_cursor = connection.cursor()
    firebird_query = """
        SELECT ec.ENDERECO_CADASTRO FROM ENDERECOS_CADASTRO ec
        WHERE ec.ENDERECO_NOTA = 'T' AND ec.GERADOR = ?
    """
    firebird_cursor.execute(firebird_query, (gerador,))
    result = firebird_cursor.fetchone()
    firebird_cursor.close()
    return result[0] if result else "Não encontrado"

# Conexão com o banco de dados MySQL
mysql_connection = mysql.connector.connect(
    host="98.142.102.10",
    user="megatoon_lojam2",
    password="hPG*r37m1B7k@Q",
    database="megatoon_lojam2"
)

# Consulta ao MySQL para obter taxvat de clientes com pedidos 'Pending'
mysql_cursor = mysql_connection.cursor(dictionary=True)
mysql_query = """
    SELECT DISTINCT ce.taxvat
    FROM customer_entity ce
    JOIN sales_order so ON ce.entity_id = so.customer_id
    WHERE so.status = 'Pending' AND ce.taxvat IS NOT NULL
"""
mysql_cursor.execute(mysql_query)
customers = mysql_cursor.fetchall()

# Fechar a conexão com o MySQL
mysql_cursor.close()
mysql_connection.close()

# Conexão com o banco de dados Firebird
firebird_connection = fdb.connect(
    dsn='milleniumflexmetal.ddns.net:C:\\SYS\\BASE\\Millennium',
    user='SYSDBA',
    password='masterkey'
)

# Verificação dos taxvat dos clientes no Firebird e consulta do endereço cadastrado
for customer in customers:
    taxvat_value = customer['taxvat']
    cliente_info = obter_cliente_firebird_por_taxvat(taxvat_value, firebird_connection)
    if cliente_info[0]:
        nome_cliente, gerador = cliente_info
        endereco_cadastro = buscar_endereco_cadastro(gerador, firebird_connection)
        print(f"CPF/CNPJ/CGC {taxvat_value} encontrado no Firebird com o ID '{nome_cliente}', gerador '{gerador}'. Endereço de cadastro: '{endereco_cadastro}'")
    else:
        print(f"CPF/CNPJ/CGC {taxvat_value} não encontrado no Firebird")

# Fechar a conexão com o Firebird
firebird_connection.close()
