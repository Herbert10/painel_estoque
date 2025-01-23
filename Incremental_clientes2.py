import pyfirebirdsql
import pymysql
import schedule
import time

# Função para obter a última ID do cliente no banco de dados MySQL
def get_last_client_id_mysql():
    connection = pymysql.connect(host='127.53.140.202', user='alfada30_DW_MEGA', password='Alfa000000!@#', database='alfada30_DW_MEGA')
    cursor = connection.cursor()
    cursor.execute("SELECT MAX(cliente) FROM Dclientes")
    result = cursor.fetchone()
    connection.close()
    return result[0] if result[0] else 0

# Função para buscar novos clientes no banco de dados Firebird
def get_new_clients_firebird(last_client_id):
    connection = pyfirebirdsql.connect(dsn='milleniumflexmetal.ddns.net:c:\\sys\\base\\millennium', user='SYSDBA', password='masterkey')
    cursor = connection.cursor()
    query = """
    SELECT cl.gerador, cl.cod_cliente, cl.cliente, cl.nome, cl.cnpj, cl.cgc, cl.cpf, cl.pf_pj, cl.data_cadastro, 
           cl.data_atualizacao, cl.e_mail, cl.desativado, cl.bloqueia_pedidos, cl.bloqueia_vendas, 
           cfc.descricao as tipo_cliente, gpl.nome as Grupo_lojas, fun.nome as Vendedor_Cadastro, cl.funcionario, 
           ec.logradouro2 AS LOGRADOURO, ec.numero, ec.cep, ec.bairro, ec.cidade, ec.estado, 
           COALESCE(cl.grupo_loja, cl.CLIENTE) AS ID_GRUPO_CLIENTE_OU_CLIENTE, 
           CASE WHEN gpl.nome IS NULL OR gpl.nome = 'INDEFINIDO' THEN cl.nome ELSE gpl.nome END AS CLIENTE_GRUPO
      FROM clientes cl
      LEFT OUTER JOIN classificacao_cliente cfc ON (cl.clscliente=cfc.clscliente)
      LEFT OUTER JOIN grupo_lojas gpl ON (cl.grupo_loja=gpl.grupo_loja)
      LEFT OUTER JOIN funcionarios fun ON (cl.funcionario=fun.funcionario)
      LEFT OUTER JOIN enderecos_cadastro ec ON (cl.gerador=ec.gerador)
     WHERE ec.endereco_nota='T' AND cl.cliente > ?
    """
    cursor.execute(query, (last_client_id,))
    new_clients = cursor.fetchall()
    connection.close()
    return new_clients

# Função para inserir novos clientes no banco de dados MySQL
def insert_clients_mysql(clients):
    if not clients:
        return
    connection = pymysql.connect(host='177.53.140.207', user='alfada30_DW_MEGA', password='Alfa211200!@#', database='alfada30_DW_MEGA')
    cursor = connection.cursor()
    query = """
    INSERT INTO Dclientes (gerador, cod_cliente, cliente, nome, cnpj, cgc, cpf, pf_pj, data_cadastro, 
                           data_atualizacao, e_mail, desativado, bloqueia_pedidos, bloqueia_vendas, 
                           tipo_cliente, Grupo_lojas, Vendedor_Cadastro, funcionario, LOGRADOURO, numero, 
                           cep, bairro, cidade, estado, ID_GRUPO_CLIENTE_OU_CLIENTE, CLIENTE_GRUPO)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.executemany(query, clients)
    connection.commit()
    connection.close()

# Função principal para a rotina de verificação e inserção
def check_and_update_clients():
    last_client_id = get_last_client_id_mysql()
    new_clients = get_new_clients_firebird(last_client_id)
    insert_clients_mysql(new_clients)

# Agendar a rotina para executar a cada 2 minutos
schedule.every(2).minutes.do(check_and_update_clients)

# Executar a rotina agendada
while True:
    schedule.run_pending()
    time.sleep(1)
