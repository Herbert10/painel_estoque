import fdb
import mysql.connector
import os
import csv
from datetime import datetime

# Função ajustada para converter string de data/hora em objeto datetime ou retornar None para valores None
def str_to_datetime(date_str):
    if date_str is None:
        return None
    return datetime.strptime(date_str, '%Y-%m-%d %H:%M')

# Conexão com o banco Firebird
con_firebird = fdb.connect(dsn='MILLENIUMFLEXMETAL.DDNS.NET:c:/sys/base/millennium',
                           user='SYSDBA', password='masterkey')

# Conexão com o banco MySQL
con_mysql = mysql.connector.connect(host='177.53.140.207', database='alfada30_Megatoon',
                                    user='alfada30_Megatoon', password='Mega211200!@#')

# Query para o Firebird
query_firebird = """
SELECT cl.gerador, 
       EXTRACT(YEAR FROM cl.data_atualizacao) || '-' || 
       LPAD(EXTRACT(MONTH FROM cl.data_atualizacao), 2, '0') || '-' || 
       LPAD(EXTRACT(DAY FROM cl.data_atualizacao), 2, '0') || ' ' || 
       LPAD(EXTRACT(HOUR FROM cl.data_atualizacao), 2, '0') || ':' || 
       LPAD(EXTRACT(MINUTE FROM cl.data_atualizacao), 2, '0') AS data_atualizacao
FROM clientes cl
LEFT OUTER JOIN enderecos_cadastro ec ON cl.gerador = ec.gerador
WHERE ec.endereco_nota = 'T'
"""

# Query para o MySQL
query_mysql = """
SELECT gerador, DATE_FORMAT(data_atualizacao, '%Y-%m-%d %H:%i') AS data_atualizacao
FROM dClientes
"""

# Executa as queries e armazena os resultados
cursor_fb = con_firebird.cursor()
cursor_fb.execute(query_firebird)
registros_fb = cursor_fb.fetchall()

cursor_my = con_mysql.cursor()
cursor_my.execute(query_mysql)
registros_my = cursor_my.fetchall()

# Convertendo registros MySQL para um dicionário para facilitar a comparação
registros_my_dict = {str(reg[0]): str_to_datetime(reg[1]) for reg in registros_my}

# Lista para armazenar os geradores
geradores = []

# Verifica as diferenças e armazena os geradores, exceto o gerador -2000000000
for reg_fb in registros_fb:
    gerador, data_atualizacao_fb_str = reg_fb
    # Ignora o gerador com o valor -2000000000
    if gerador == -2000000000:
        continue  # Pula para o próximo registro sem processar este
    data_atualizacao_fb = str_to_datetime(data_atualizacao_fb_str)
    data_atualizacao_my = registros_my_dict.get(str(gerador))
    if data_atualizacao_my is not None and data_atualizacao_fb is not None:
        if abs((data_atualizacao_fb - data_atualizacao_my).total_seconds()) >= 90:
            geradores.append(str(gerador))  # Certifique-se de que gerador é uma string
    elif data_atualizacao_my is None or data_atualizacao_fb is None:
        geradores.append(str(gerador))  # Certifique-se de que gerador é uma string


# Junta os geradores em uma string, separados por vírgula
geradores_str = ','.join(geradores)

if geradores_str:  # Verifica se a string não está vazia
    query_firebird_detalhada = f"""
    SELECT cl.gerador, cl.cod_cliente, cl.cliente, cl.nome, cl.cnpj, cl.cgc, cl.cpf, cl.pf_pj, cl.data_cadastro, cl.data_atualizacao, cl.e_mail, cl.desativado,
           cl.bloqueia_pedidos, cl.bloqueia_vendas, cfc.descricao AS tipo_cliente, gpl.nome AS Grupo_lojas, fun.nome AS Vendedor_Cadastro, cl.funcionario,
           ec.logradouro2 AS LOGRADOURO, ec.numero, ec.cep, ec.bairro, ec.cidade, ec.estado
    FROM clientes cl
    LEFT OUTER JOIN classificacao_cliente cfc ON (cl.clscliente=cfc.clscliente)
    LEFT OUTER JOIN grupo_lojas gpl ON (cl.grupo_loja=gpl.grupo_loja)
    LEFT OUTER JOIN funcionarios fun ON (cl.funcionario=fun.funcionario)
    LEFT OUTER JOIN enderecos_cadastro ec ON (cl.gerador=ec.gerador)
    WHERE ec.endereco_nota='T' AND cl.gerador IN ({geradores_str})
    """
    if geradores_str:  # Verifica se a string não está vazia
        try:
            cursor_fb = con_firebird.cursor()
            query_firebird_detalhada += f" AND cl.gerador IN ({geradores_str})"
            cursor_fb.execute(query_firebird_detalhada)
            resultados = cursor_fb.fetchall()

            # Inserção dos resultados no MySQL
            cursor_my = con_mysql.cursor()
            inserir_atualizar_sql = """
            INSERT INTO dClientes (gerador, cod_cliente, cliente, nome, cnpj, cgc, cpf, pf_pj, data_cadastro, data_atualizacao, e_mail, desativado, bloqueia_pedidos, bloqueia_vendas, tipo_cliente, Grupo_lojas, Vendedor_Cadastro, funcionario, LOGRADOURO, numero, cep, bairro, cidade, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE cod_cliente = VALUES(cod_cliente), cliente = VALUES(cliente), nome = VALUES(nome), cnpj = VALUES(cnpj), cgc = VALUES(cgc), cpf = VALUES(cpf), pf_pj = VALUES(pf_pj), data_cadastro = VALUES(data_cadastro), data_atualizacao = VALUES(data_atualizacao), e_mail = VALUES(e_mail), desativado = VALUES(desativado), bloqueia_pedidos = VALUES(bloqueia_pedidos), bloqueia_vendas = VALUES(bloqueia_vendas), tipo_cliente = VALUES(tipo_cliente), Grupo_lojas = VALUES(Grupo_lojas), Vendedor_Cadastro = VALUES(Vendedor_Cadastro), funcionario = VALUES(funcionario), LOGRADOURO = VALUES(LOGRADOURO), numero = VALUES(numero), cep = VALUES(cep), bairro = VALUES(bairro), cidade = VALUES(cidade), estado = VALUES(estado);
            """
            for row in resultados:
                cursor_my.execute(inserir_atualizar_sql, row)
            con_mysql.commit()
            print(f"{cursor_my.rowcount} registros processados com sucesso na tabela dClientes.")

        except Exception as e:
            print(f"Ocorreu um erro: {e}")
        finally:
            cursor_fb.close()
            cursor_my.close()  # Garante que o cursor do MySQL também seja fechado
            con_firebird.close()
