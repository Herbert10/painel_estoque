from flask import Flask, render_template, request, jsonify, session
import os
import psycopg2
import requests
import json
from dotenv import load_dotenv
from datetime import datetime
from urllib.parse import quote

# Carregar variáveis do arquivo .env
load_dotenv()

app = Flask(__name__)
app.secret_key = 'chave_secreta'

# Configurações da Z-API (carregadas do .env)
ZAPI_URL_BASE = os.getenv("ZAPI_URL_BASE")
CLIENT_TOKEN = os.getenv("CLIENT_TOKEN")

# Configurações do Banco de Dados
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Função para conectar ao banco de dados
def conectar_banco():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

@app.route('/')
def selecionar_cliente():
    return render_template('cliente.html')

@app.route('/buscar-vendedores', methods=['GET'])
def buscar_vendedores():
    try:
        conn = conectar_banco()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT vendedor_cadastro FROM megatoon.dclientes WHERE vendedor_cadastro IS NOT NULL")
        vendedores = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify(vendedores)
    except Exception as e:
        print(f"Erro ao buscar vendedores: {e}")
        return jsonify([])

@app.route('/buscar-cliente', methods=['GET'])
def buscar_cliente():
    codigo = request.args.get('codigo')
    nome = request.args.get('nome')
    vendedor = request.args.get('vendedor')

    try:
        conn = conectar_banco()
        cursor = conn.cursor()

        query = """
            SELECT 
                c.id_cliente, 
                c.cod_cliente, 
                c.nome_cliente, 
                c.classificacao_cliente, 
                MAX(r.data_ultima_compra) AS ultima_compra,
                COUNT(r.ptc) AS qtd_produtos
            FROM megatoon.dclientes c
            LEFT JOIN megatoon.recomendacao_historico r ON c.id_cliente = r.cliente_id
            WHERE (%s IS NULL OR c.cod_cliente = %s)
              AND (%s IS NULL OR c.nome_cliente ILIKE %s)
              AND (%s IS NULL OR TRIM(UPPER(c.vendedor_cadastro)) = TRIM(UPPER(%s)))
            GROUP BY c.id_cliente, c.cod_cliente, c.nome_cliente, c.classificacao_cliente
        """
        cursor.execute(query, (
            codigo if codigo else None,
            codigo if codigo else None,
            nome if nome else None,
            f"%{nome}%" if nome else None,
            vendedor if vendedor else None,
            vendedor if vendedor else None
        ))

        resultados = cursor.fetchall()
        clientes = []
        for row in resultados:
            clientes.append({
                "id": row[0],
                "codigo": row[1],
                "nome": row[2],
                "classificacao": row[3],
                "ultima_compra": row[4].strftime("%d/%m/%Y") if row[4] else "N/A",
                "qtd_produtos": row[5]
            })

        cursor.close()
        conn.close()
        return jsonify(clientes)

    except Exception as e:
        print(f"Erro ao buscar clientes: {e}")
        return jsonify([])

@app.route('/produtos/<int:cliente_id>')
def listar_produtos(cliente_id):
    try:
        conn = conectar_banco()
        cursor = conn.cursor()
        query = "SELECT nome_cliente FROM megatoon.dclientes WHERE id_cliente = %s"
        cursor.execute(query, (cliente_id,))
        resultado = cursor.fetchone()

        if resultado:
            session['cliente_id'] = cliente_id
            session['cliente_nome'] = resultado[0]
        else:
            print(f"Cliente ID {cliente_id} não encontrado!")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Erro ao buscar nome do cliente: {e}")

    return render_template('produtos.html')

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
                   estoque_sp, rank_recomendacao, data_primeira_compra, data_ultima_compra,
                   produto_url
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
                "data_ultima_compra": row[7].strftime("%d/%m/%Y") if row[7] else "N/A",
                "produto_url": row[8] or "www.megatoon.org"  # Use fallback URL if produto_url is NULL
            })

        cursor.close()
        conn.close()
        return jsonify(produtos)

    except Exception as e:
        print(f"Erro ao buscar produtos: {e}")
        return jsonify([])

@app.route('/enviar-mensagem', methods=['POST'])
def enviar_mensagem():
    data = request.json
    print("Dados recebidos no backend:", json.dumps(data, indent=4))  # Log dos dados recebidos

    observacao = data.get('observacao', '')
    imagens = data.get('imagens', [])
    descricoes = data.get('descricoes', [])
    urls = data.get('urls', [])  # URLs correspondentes aos produtos

    if not imagens or not descricoes:
        return jsonify({"error": "Nenhuma imagem ou descrição foi enviada"}), 400

    headers = {
        "Content-Type": "application/json",
        "Client-Token": CLIENT_TOKEN
    }

    try:
        # Enviar a observação como mensagem de texto
        if observacao:
            payload_text = {
                "phone": "5511981154100",  # Número do destinatário
                "message": observacao     # Observação a ser enviada
            }

            endpoint_text = f"{ZAPI_URL_BASE}/send-text"
            response_text = requests.post(endpoint_text, json=payload_text, headers=headers)

            if response_text.status_code != 200:
                return jsonify({"error": f"Falha ao enviar observação: {response_text.text}"}), 500

        # Enviar cada imagem com sua respectiva descrição e URL
        for imagem_url, descricao, produto_url in zip(imagens, descricoes, urls):
            # Adicionar a URL ao final da descrição
            descricao_com_url = f"{descricao}\n{produto_url or 'www.megatoon.org'}"  # URL com fallback

            payload_image = {
                "phone": "5511941445959",  # Número do destinatário
                "image": imagem_url,       # URL da imagem
                "caption": descricao_com_url  # Legenda da imagem com URL
            }

            endpoint_image = f"{ZAPI_URL_BASE}/send-image"
            response_image = requests.post(endpoint_image, json=payload_image, headers=headers)

            if response_image.status_code != 200:
                return jsonify({"error": f"Falha ao enviar imagem: {response_image.text}"}), 500

        return jsonify({"message": "Observação e imagens enviadas com sucesso!"})

    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")
        return jsonify({"error": "Erro ao enviar mensagem"}), 500

if __name__ == '__main__':
    app.run(debug=True)