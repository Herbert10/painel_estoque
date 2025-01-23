import mysql.connector
import fdb
import json
import os

def conectar_mysql():
    try:
        conn = mysql.connector.connect(
            host='98.142.102.10',
            user='megatoon_lojam2',
            password='hPG*r37m1B7k@Q',
            database='megatoon_lojam2'
        )
        return conn
    except mysql.connector.Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
        return None

def conectar_firebird():
    try:
        conn = fdb.connect(
            dsn='milleniumflexmetal.ddns.net:C:\\SYS\\BASE\\Millennium',
            user='SYSDBA',
            password='masterkey'
        )
        return conn
    except fdb.Error as e:
        print(f"Erro ao conectar ao Firebird: {e}")
        return None

def verificar_clientes_no_firebird(firebird_conn):
    cursor = firebird_conn.cursor()
    query = "SELECT cliente, CPF FROM clientes WHERE status_confirmado = 'Sim'"  # Ajuste o nome da coluna conforme necessário.
    try:
        cursor.execute(query)
        return cursor.fetchall()
    except fdb.Error as e:
        print(f"Erro ao executar consulta no Firebird: {e}")
        return []

def obter_pedidos_pendentes(mysql_conn, cpf_cliente):
    cursor = mysql_conn.cursor(dictionary=True)
    query = f"SELECT * FROM sales_order WHERE status = 'Pending' AND taxvat = '{cpf_cliente}'"
    try:
        cursor.execute(query)
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Erro ao executar consulta no MySQL: {e}")
        return []

mysql_conn = conectar_mysql()
firebird_conn = conectar_firebird()

if mysql_conn and firebird_conn:
    clientes_confirmados = verificar_clientes_no_firebird(firebird_conn)
    if clientes_confirmados:
        pedidos_confirmados = []
        for cliente in clientes_confirmados:
            nome_cliente, cpf_cliente = cliente
            pedidos = obter_pedidos_pendentes(mysql_conn, cpf_cliente)
            for pedido in pedidos:
                pedido['cliente_nome'] = nome_cliente
                pedidos_confirmados.append(pedido)
                print(f"Pedido confirmado para o cliente {nome_cliente} com CPF {cpf_cliente}.")

        # Salvar os pedidos confirmados em JSON
        caminho_arquivo = os.path.join('C:\\dados', 'pedidos_confirmados.json')
        with open(caminho_arquivo, 'w', encoding='utf-8') as file:
            json.dump(pedidos_confirmados, file, ensure_ascii=False, indent=4)
        print(f"Arquivo JSON salvo em {caminho_arquivo}.")
    else:
        print("Nenhum cliente confirmado encontrado no Firebird.")

    mysql_conn.close()
    firebird_conn.close()
else:
    print("Não foi possível estabelecer conexão com os bancos de dados.")
