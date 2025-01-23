import fdb
import mysql.connector
from datetime import datetime, timedelta

# Função para ler a última data de atualização processada
def ler_ultima_data_processada():
    try:
        with open("ultima_data.txt", "r") as file:
            return datetime.fromisoformat(file.read().strip())
    except FileNotFoundError:
        return None

# Função para salvar a última data de atualização processada
def salvar_ultima_data_processada(data):
    with open("ultima_data.txt", "w") as file:
        file.write(data.isoformat())

# Configurações de conexão ao Firebird
firebird_conn = fdb.connect(
    dsn='milleniumflexmetal.ddns.net:c:/SYS/base/millennium',  # Ajuste para o caminho do seu banco Firebird
    user='SYSDBA',
    password='masterkey'
)

# Configurações de conexão ao MySQL
mysql_conn = mysql.connector.connect(
    host='177.53.140.207',
    database='alfada30_DW_MEGA',
    user='alfada30_DW_MEGA',
    password='Alfa211200!@#'
)

# Cursor para Firebird
fb_cursor = firebird_conn.cursor()
# Cursor para MySQL
mysql_cursor = mysql_conn.cursor()

# Verifica a última data de atualização processada
ultima_data_processada = ler_ultima_data_processada()

# Define o intervalo de 90 dias
data_limite = datetime.now() - timedelta(days=90)

# Se não houver uma data anterior, traz os dados dos últimos 90 dias
if ultima_data_processada is None:
    query = f"""
        SELECT cl.gerador, cl.cod_cliente, cl.cliente, cl.nome, cl.cnpj, cl.cgc, cl.cpf, cl.pf_pj,
               cl.data_cadastro, cl.data_atualizacao, cl.e_mail, cl.desativado, cl.bloqueia_pedidos,
               cl.bloqueia_vendas, cfc.descricao AS tipo_cliente, gpl.nome AS Grupo_lojas,
               fun.nome AS Vendedor_Cadastro, cl.funcionario, ec.logradouro2 AS LOGRADOURO, 
               ec.numero, ec.cep, ec.bairro, ec.cidade, ec.estado, EC.endereco_cadastro, 
               COALESCE(cl.grupo_loja, cl.CLIENTE) AS ID_GRUPO_CLIENTE_OU_CLIENTE,
               CASE WHEN gpl.nome IS NULL OR gpl.nome = 'INDEFINIDO' THEN cl.nome ELSE gpl.nome END AS CLIENTE_GRUPO
        FROM clientes cl
        LEFT OUTER JOIN classificacao_cliente cfc ON (cl.clscliente = cfc.clscliente)
        LEFT OUTER JOIN grupo_lojas gpl ON (cl.grupo_loja = gpl.grupo_loja)
        LEFT OUTER JOIN funcionarios fun ON (cl.funcionario = fun.funcionario)
        LEFT OUTER JOIN enderecos_cadastro ec ON (cl.gerador = ec.gerador)
        WHERE ec.endereco_nota = 'T' AND cl.data_atualizacao >= '{data_limite.strftime('%Y-%m-%d %H:%M:%S')}'
    """
else:
    # Caso contrário, traz apenas os dados atualizados desde a última data processada
    query = f"""
        SELECT cl.gerador, cl.cod_cliente, cl.cliente, cl.nome, cl.cnpj, cl.cgc, cl.cpf, cl.pf_pj,
               cl.data_cadastro, cl.data_atualizacao, cl.e_mail, cl.desativado, cl.bloqueia_pedidos,
               cl.bloqueia_vendas, cfc.descricao AS tipo_cliente, gpl.nome AS Grupo_lojas,
               fun.nome AS Vendedor_Cadastro, cl.funcionario, ec.logradouro2 AS LOGRADOURO, 
               ec.numero, ec.cep, ec.bairro, ec.cidade, ec.estado, EC.endereco_cadastro, 
               COALESCE(cl.grupo_loja, cl.CLIENTE) AS ID_GRUPO_CLIENTE_OU_CLIENTE,
               CASE WHEN gpl.nome IS NULL OR gpl.nome = 'INDEFINIDO' THEN cl.nome ELSE gpl.nome END AS CLIENTE_GRUPO
        FROM clientes cl
        LEFT OUTER JOIN classificacao_cliente cfc ON (cl.clscliente = cfc.clscliente)
        LEFT OUTER JOIN grupo_lojas gpl ON (cl.grupo_loja = gpl.grupo_loja)
        LEFT OUTER JOIN funcionarios fun ON (cl.funcionario = fun.funcionario)
        LEFT OUTER JOIN enderecos_cadastro ec ON (cl.gerador = ec.gerador)
        WHERE ec.endereco_nota = 'T' AND cl.data_atualizacao > '{ultima_data_processada.strftime('%Y-%m-%d %H:%M:%S')}'
    """

# Executa a consulta no Firebird
fb_cursor.execute(query)
rows = fb_cursor.fetchall()

# Função para tratar a conversão de dados
def tratar_dados(row):
    processed_row = []
    for value in row:
        if isinstance(value, bytes):
            processed_row.append(value.decode('utf-8', 'ignore'))  # Trata possíveis problemas de codificação
        else:
            processed_row.append(value)
    return processed_row

# Inserção no MySQL
insert_query = """
    INSERT INTO dClientes (gerador, cod_cliente, cliente, nome, cnpj, cgc, cpf, pf_pj, data_cadastro, 
                                data_atualizacao, e_mail, desativado, bloqueia_pedidos, bloqueia_vendas, 
                                tipo_cliente, Grupo_lojas, Vendedor_Cadastro, funcionario, LOGRADOURO, numero, 
                                cep, bairro, cidade, estado, endereco_cadastro, ID_GRUPO_CLIENTE_OU_CLIENTE, 
                                CLIENTE_GRUPO) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

# Itera sobre os resultados e insere no MySQL
for row in rows:
    mysql_cursor.execute(insert_query, tratar_dados(row))

# Confirma as transações no MySQL
mysql_conn.commit()

# Atualiza a data da última atualização processada
salvar_ultima_data_processada(datetime.now())

# Fecha as conexões
fb_cursor.close()
firebird_conn.close()
mysql_cursor.close()
mysql_conn.close()

print("Transferência de dados incremental concluída com sucesso!")
