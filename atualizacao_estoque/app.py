import pandas as pd
import os
import fdb
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from flask_caching import Cache

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Configuração do cache
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

def buscar_dados_firebird(cod_cliente, data_inicial, data_final):
    con = fdb.connect(
        dsn='localhost:C:\\sys\\base\\millennium',
        user='SYSDBA',
        password='masterkey'
    )
    cur = con.cursor()

    query = f"""
    SELECT 
        C.COD_CLIENTE,
        C.NOME,
        P.COD_PRODUTO,
        P.DESCRICAO1 AS DESCRICAO,
        C2.COD_COR,
        C2.DESCRICAO AS COR,
        PE.TAMANHO,
        (PE.PRODUTO || '-' || PE.TAMANHO || '-' || PE.COR) AS PTC,
        SUM(PE.QUANTIDADE) AS QUANTIDADE,
        PE.PRECO,
        'https://megatoon.com.br/imagens_produtos/' || P.COD_PRODUTO || '_' || PE.TAMANHO || '_' || C2.COD_COR || '.jpg' AS FOTO
    FROM 
        PRODUTOS_EVENTOS PE
    LEFT OUTER JOIN 
        MOVIMENTO M ON (PE.COD_OPERACAO=M.COD_OPERACAO AND PE.TIPO_OPERACAO=M.TIPO_OPERACAO)
    LEFT OUTER JOIN 
        CLIENTES C ON M.CLIENTE = C.CLIENTE
    LEFT OUTER JOIN 
        PRODUTOS P ON PE.PRODUTO = P.PRODUTO
    LEFT OUTER JOIN 
        CORES C2 ON PE.COR = C2.COR
    WHERE 
        M."DATA" BETWEEN '{data_inicial}' AND '{data_final}'
        AND C.COD_CLIENTE = '{cod_cliente}'
    GROUP BY 
        C.COD_CLIENTE, C.NOME, P.COD_PRODUTO, P.DESCRICAO1, C2.COD_COR, C2.DESCRICAO, PE.TAMANHO, (PE.PRODUTO || '-' || PE.TAMANHO || '-' || PE.COR), PE.PRECO, P.COD_PRODUTO, PE.PRODUTO, C2.COD_COR
    ORDER BY 
        P.COD_PRODUTO, C2.DESCRICAO
    """

    cur.execute(query)
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    con.close()

    df = pd.DataFrame(rows, columns=colnames)
    return df

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('upload.html')

@app.route('/buscar', methods=['POST'])
@cache.cached(timeout=300, query_string=True)
def buscar():
    cod_cliente = request.form['cod_cliente']
    data_inicial = request.form['data_inicial']
    data_final = request.form['data_final']
    filename = 'dados.xlsx'  # Defina um nome padrão para o arquivo

    df = buscar_dados_firebird(cod_cliente, data_inicial, data_final)
    return render_template('formulario.html', df=df, titles=df.columns.values, filename=filename, cod_cliente=cod_cliente, data_inicial=data_inicial, data_final=data_final)

@app.route('/romaneios', methods=['POST'])
def romaneios():
    cod_cliente = request.form['cod_cliente']
    data_inicial = request.form['data_inicial']
    data_final = request.form['data_final']

    con = fdb.connect(
        dsn='localhost:C:\\sys\\base\\millennium',
        user='SYSDBA',
        password='masterkey'
    )
    cur = con.cursor()

    query = f"""
    SELECT DISTINCT M.ROMANEIO, M."DATA"
    FROM MOVIMENTO M
    LEFT JOIN CLIENTES C ON M.CLIENTE = C.CLIENTE
    WHERE 
        M."DATA" BETWEEN '{data_inicial}' AND '{data_final}'
        AND C.COD_CLIENTE = '{cod_cliente}'
    ORDER BY M."DATA"
    """

    cur.execute(query)
    rows = cur.fetchall()
    con.close()

    romaneios = [{'romaneio': row[0], 'data': row[1].strftime('%d/%m/%Y')} for row in rows]
    return jsonify(romaneios)

@app.route('/detalhes_produto', methods=['POST'])
def detalhes_produto():
    cod_cliente = request.form['cod_cliente']
    data_inicial = request.form['data_inicial']
    data_final = request.form['data_final']
    cod_produto = request.form['cod_produto']
    cod_cor = request.form['cod_cor']
    tamanho = request.form['tamanho']

    con = fdb.connect(
        dsn='localhost:C:\\sys\\base\\millennium',
        user='SYSDBA',
        password='masterkey'
    )
    cur = con.cursor()

    query = f"""
    SELECT DISTINCT M.ROMANEIO, M."DATA", PE.QUANTIDADE, PE.PRECO
    FROM MOVIMENTO M
    LEFT JOIN PRODUTOS_EVENTOS PE ON (M.COD_OPERACAO=PE.COD_OPERACAO AND M.TIPO_OPERACAO=M.TIPO_OPERACAO)
    LEFT JOIN CLIENTES C ON M.CLIENTE = C.CLIENTE
    LEFT JOIN PRODUTOS P ON PE.PRODUTO = P.PRODUTO
    LEFT JOIN CORES C2 ON PE.COR = C2.COR
    WHERE 
        M."DATA" BETWEEN '{data_inicial}' AND '{data_final}'
        AND C.COD_CLIENTE = '{cod_cliente}'
        AND P.COD_PRODUTO = '{cod_produto}'
        AND C2.COD_COR = '{cod_cor}'
        AND PE.TAMANHO = '{tamanho}'
    ORDER BY M."DATA"
    """

    cur.execute(query)
    rows = cur.fetchall()
    con.close()

    detalhes = [{'romaneio': row[0], 'data': row[1].strftime('%d/%m/%Y'), 'quantidade': row[2], 'preco': row[3]} for row in rows]
    return jsonify(detalhes)

@app.route('/salvar/<filename>', methods=['POST'])
def salvar(filename):
    dados_formulario = request.form.to_dict(flat=False)

    # Captura os valores preenchidos no formulário
    estoque_atual = dados_formulario.get('estoque_atual', [])
    reposicao = dados_formulario.get('reposicao', [])

    # Captura os dados da tabela
    cod_produto = dados_formulario.get('cod_produto', [])
    cod_cor = dados_formulario.get('cod_cor', [])
    tamanho = dados_formulario.get('tamanho', [])
    quantidade = dados_formulario.get('quantidade', [])
    preco = dados_formulario.get('preco', [])
    foto = dados_formulario.get('foto', [])

    data = {
        'COD_PRODUTO': cod_produto,
        'COD_COR': cod_cor,
        'TAMANHO': tamanho,
        'COD_ESTAMPA': ['000'] * len(cod_produto),
        'QUANTIDADE': quantidade,
        'PRECO': preco,
        'FOTO': foto,
        'ESTOQUE_ATUAL': estoque_atual,
        'REPOSICAO': reposicao
    }

    df = pd.DataFrame(data)

    if len(df.columns) > 0:
        output_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df.to_excel(output_filepath, index=False)
        return send_file(output_filepath, as_attachment=True)
    else:
        return 'Nenhum dado para salvar'

if __name__ == '__main__':
    app.run(debug=True)
