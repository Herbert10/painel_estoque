from flask import Flask, render_template, request, jsonify, session
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
from dotenv import load_dotenv
from datetime import datetime
import json

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
app.secret_key = 'chave_secreta'

# Configurações do banco de dados
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Configurações da Z-API
ZAPI_URL = os.getenv("ZAPI_URL")
ZAPI_TOKEN = os.getenv("ZAPI_TOKEN")

# Função para conectar ao banco de dados
def conectar_banco():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

# Função para registrar envio no banco de dados
def registrar_envio(cliente_id, cliente_nome, imagens, descricoes, observacao):
    try:
        conn = conectar_banco()
        cursor = conn.cursor()

        produtos = [{"imagem": img, "descricao": desc} for img, desc in zip(imagens, descricoes)]

        query = """
            INSERT INTO megatoon.envios_whatsapp (cliente_id, cliente_nome, produtos, observacao, data_envio)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (cliente_id, cliente_nome, json.dumps(produtos), observacao, datetime.now()))
        conn.commit()

        cursor.close()
        conn.close()
        print("Log de envio registrado com sucesso!")
    except Exception as e:
        print(f"Erro ao registrar envio no banco: {e}")

# Rota principal para selecionar clientes
@app.route('/')
def selecionar_cliente():
    return render_template('clientes.html')

# Rota para buscar vendedores no banco de dados
@app.route('/buscar-vendedores', methods=['GET'])
def buscar_vendedores():
    try:
        conn = conectar_banco()
        cursor = conn.cursor()
        query = "SELECT DISTINCT vendedor_cadastro FROM megatoon.dclientes WHERE vendedor_cadastro IS NOT NULL"
        cursor.execute(query)
        vendedores = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify(vendedores)
    except Exception as e:
        print(f"Erro ao buscar vendedores: {e}")
        return jsonify([])

# Rota para buscar clientes no banco de dados
@app.route('/buscar-cliente', methods=['GET'])
def buscar_cliente():
    codigo = request.args.get('codigo', '')
    nome = request.args.get('nome', '')
    vendedor = request.args.get('vendedor', '')

    try:
        conn = conectar_banco()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT 
                c.cod_cliente, 
                c.nome_cliente, 
                c.classificacao_cliente, 
                MAX(r.data_ultima_compra) AS ultima_compra,
                COUNT(r.ptc) AS qtd_produtos
            FROM megatoon.dclientes c
            LEFT JOIN megatoon.recomendacao_historico r ON c.id_cliente = r.cliente_id
            WHERE (%s = '' OR c.cod_cliente::TEXT = %s)
              AND (%s = '' OR c.nome_cliente ILIKE %s)
              AND (%s = '' OR c.vendedor_cadastro ILIKE %s)
            GROUP BY c.cod_cliente, c.nome_cliente, c.classificacao_cliente
        """
        cursor.execute(query, (codigo, codigo, nome, f"%{nome}%", vendedor, f"%{vendedor}%"))
        resultados = cursor.fetchall()

        clientes = []
        for row in resultados:
            clientes.append({
                "cod_cliente": row['cod_cliente'],
                "nome_cliente": row['nome_cliente'],
                "classificacao_cliente": row['classificacao_cliente'],
                "ultima_compra": row['ultima_compra'].strftime('%d/%m/%Y') if row['ultima_compra'] else "N/A",
                "qtd_produtos": row['qtd_produtos']
            })

        cursor.close()
        conn.close()
        return jsonify(clientes)

    except Exception as e:
        print(f"Erro ao buscar clientes: {e}")
        return jsonify([])

# Rota para exibir produtos de um cliente
@app.route('/produtos/<int:cliente_id>')
def listar_produtos(cliente_id):
    try:
        session['cliente_id'] = cliente_id  # Salva o ID do cliente na sessão

        # Conexão ao banco
        conn = conectar_banco()
        cursor = conn.cursor()

        # Busca os produtos do cliente na view recomendacao_historico
        query = """
            SELECT 
                cliente_nome, 
                produto_nome, 
                foto_produto, 
                qtd_comprada, 
                total_vendido, 
                estoque_sp, 
                data_primeira_compra, 
                data_ultima_compra, 
                rank_recomendacao
            FROM megatoon.recomendacao_historico
            WHERE cliente_id = %s
            ORDER BY rank_recomendacao ASC
        """
        cursor.execute(query, (cliente_id,))
        resultados = cursor.fetchall()

        # Processa os resultados
        produtos = []
        for row in resultados:
            produtos.append({
                "cliente_nome": row[0],
                "produto_nome": row[1],
                "foto_produto": row[2],
                "qtd_comprada": row[3],
                "total_vendido": row[4],
                "estoque_sp": row[5],
                "data_primeira_compra": row[6].strftime('%d/%m/%Y') if row[6] else "N/A",
                "data_ultima_compra": row[7].strftime('%d/%m/%Y') if row[7] else "N/A",
                "rank_recomendacao": row[8]
            })

        cursor.close()
        conn.close()

        if not produtos:
            return render_template(
                'produtos.html',
                cliente_nome="Nenhum cliente encontrado",
                produtos=[],
                mensagem="Nenhum produto encontrado."
            )

        return render_template(
            'produtos.html',
            cliente_nome=produtos[0]['cliente_nome'],
            produtos=produtos,
            mensagem=""
        )

    except Exception as e:
        print(f"Erro ao listar produtos: {e}")
        return render_template(
            'produtos.html',
            cliente_nome="Erro",
            produtos=[],
            mensagem="Erro ao buscar produtos."
        )

@app.route('/buscar-produtos', methods=['GET'])
def buscar_produtos():
    cliente_id = session.get('cliente_id')

    if not cliente_id:
        return jsonify([])

    try:
        conn = conectar_banco()
        cursor = conn.cursor()

        query = """
            SELECT produto_nome, foto_produto, qtd_comprada, total_vendido,
                   estoque_sp, rank_recomendacao, data_primeira_compra, data_ultima_compra
            FROM megatoon.recomendacao_historico
            WHERE cliente_id = %s
            ORDER BY rank_recomendacao ASC
        """
        cursor.execute(query, (cliente_id,))
        resultados = cursor.fetchall()

        produtos = []
        for row in resultados:
            produtos.append({
                "produto_nome": row[0],
                "foto_produto": row[1],
                "qtd_comprada": row[2],
                "total_vendido": row[3],
                "estoque_sp": row[4],
                "rank_recomendacao": row[5],
                "data_primeira_compra": row[6].strftime("%d/%m/%Y") if row[6] else "N/A",
                "data_ultima_compra": row[7].strftime("%d/%m/%Y") if row[7] else "N/A"
            })

        cursor.close()
        conn.close()
        return jsonify(produtos)

    except Exception as e:
        print(f"Erro ao buscar produtos: {e}")
        return jsonify([])


# Rota para enviar mensagem via Z-API
@app.route('/enviar-mensagem', methods=['POST'])
def enviar_mensagem():
    data = request.json
    observacao = data.get('observacao')
    imagens = data.get('imagens')
    descricoes = data.get('descricoes')
    cliente_id = session.get('cliente_id')
    cliente_nome = session.get('cliente_nome')

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ZAPI_TOKEN}"
    }

    # Envia a observação como mensagem de texto
    payload_text = {
        "phone": "5511941445959",  # Número no formato internacional
        "message": f"Cliente: {cliente_nome}\n\nObservação: {observacao}"
    }
    response_text = requests.post(f"{ZAPI_URL}/send-message", json=payload_text, headers=headers)

    if response_text.status_code != 200:
        print(f"Erro ao enviar mensagem de texto: {response_text.text}")
        return jsonify({"error": "Falha ao enviar mensagem de texto"}), 500

    # Envia imagens com descrições
    for imagem, descricao in zip(imagens, descricoes):
        payload_image = {
            "phone": "5511941445959",
            "image": imagem,
            "caption": descricao
        }
        response_image = requests.post(f"{ZAPI_URL}/send-image", json=payload_image, headers=headers)

        if response_image.status_code != 200:
            print(f"Erro ao enviar imagem: {response_image.text}")
            return jsonify({"error": "Falha ao enviar uma ou mais imagens"}), 500

    # Registrar envio no banco de dados
    registrar_envio(cliente_id, cliente_nome, imagens, descricoes, observacao)

    return jsonify({"message": "Mensagem enviada com sucesso!"})

if __name__ == '__main__':
    app.run(debug=True)
