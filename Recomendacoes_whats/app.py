from flask import Flask, render_template, request, jsonify, session
import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'sua_chave_secreta')  # Forma mais segura de lidar com a chave secreta

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

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
              AND (%s IS NULL OR c.vendedor_cadastro = %s) -- Corrigido aqui!
            GROUP BY c.id_cliente, c.cod_cliente, c.nome_cliente, c.classificacao_cliente
        """
        cursor.execute(query, (codigo, codigo, nome, f"%{nome}%" if nome else None, vendedor, vendedor))
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
        print("Erro: cliente_id não definido na sessão!")
        return jsonify([])

    try:
        conn = conectar_banco()
        cursor = conn.cursor()

        query = """
            SELECT
                r.rank_recomendacao,
                r.produto_nome,
                r.foto_produto,
                r.qtd_comprada,
                r.total_vendido,
                r.estoque_sp,
                r.data_primeira_compra,
                r.data_ultima_compra,
                c.nome_cliente  -- Nome do cliente da tabela dclientes
            FROM megatoon.recomendacao_historico r
            JOIN megatoon.dclientes c ON r.cliente_id = c.id_cliente -- JOIN para obter o nome do cliente
            WHERE r.cliente_id = %s
            ORDER BY r.rank_recomendacao ASC
        """
        cursor.execute(query, (cliente_id,))
        resultados = cursor.fetchall()

        produtos = []
        for row in resultados:
            produto = {
                "rank_recomendacao": row[0],
                "produto_nome": row[1],
                "foto_produto": row[2],
                "qtd_comprada": f"{int(row[3]):,}".replace(",", "."),
                "total_vendido": f"{int(row[4]):,}".replace(",", "."),
                "estoque_sp": f"{int(row[5]):,}".replace(",", "."),
                "data_primeira_compra": row[6].strftime("%d/%m/%Y") if row[6] else "N/A", # Formatar datas
                "data_ultima_compra": row[7].strftime("%d/%m/%Y") if row[7] else "N/A", # Formatar datas
                "cliente_nome": row[8]
            }
            produtos.append(produto)

        cursor.close()
        conn.close()
        return jsonify(produtos)

    except Exception as e:
        print(f"Erro ao buscar produtos: {e}")
        return jsonify([])


if __name__ == '__main__':
    app.run(debug=True)
