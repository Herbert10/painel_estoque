from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Função para conectar ao banco de dados SQLite
def conectar_bd():
    conn = sqlite3.connect('votacao.db')
    conn.row_factory = sqlite3.Row
    return conn


# Rota para a página de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        numero_telefone = request.form['numero_telefone']
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contatos WHERE numero_telefone = ?", (numero_telefone,))
        contato = cursor.fetchone()
        conn.close()

        if contato:
            session['numero_telefone'] = numero_telefone
            return redirect(url_for('votar'))
        else:
            flash("Número de telefone não cadastrado.", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')


# Rota para a página de votação
@app.route('/votar', methods=['GET', 'POST'])
def votar():
    if 'numero_telefone' not in session:
        return redirect(url_for('login'))

    numero_telefone = session['numero_telefone']

    if request.method == 'POST':
        variacao_id = request.form['variacao_id']
        voto = request.form['voto']
        comentario = request.form.get('comentario', '')

        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO votos (variacao_id, numero_telefone, voto, comentario)
            VALUES (?, ?, ?, ?)
        ''', (variacao_id, numero_telefone, voto, comentario))
        conn.commit()
        conn.close()

        flash("Voto registrado com sucesso!", "success")
        return redirect(url_for('votar'))

    # Carregar produtos e variações para exibição
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.descricao, p.foto_url, v.id as variacao_id, v.cor, v.tamanho
        FROM produtos p
        JOIN variacoes v ON p.id = v.produto_id
    ''')
    produtos = cursor.fetchall()
    conn.close()

    return render_template('votar.html', produtos=produtos)


# Rota para logout
@app.route('/logout')
def logout():
    session.pop('numero_telefone', None)
    return redirect(url_for('login'))


# Rota para cadastro de contatos
@app.route('/cadastro_contatos', methods=['GET', 'POST'])
def cadastro_contatos():
    if request.method == 'POST':
        numero_telefone = request.form['numero_telefone']
        nome = request.form['nome']

        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO contatos (numero_telefone, nome)
            VALUES (?, ?)
        ''', (numero_telefone, nome))
        conn.commit()
        conn.close()

        flash("Contato cadastrado com sucesso!", "success")
        return redirect(url_for('cadastro_contatos'))

    return render_template('cadastro_contatos.html')


# Rota para cadastro de produtos e suas variações
@app.route('/cadastro_produtos', methods=['GET', 'POST'])
def cadastro_produtos():
    if request.method == 'POST':
        descricao = request.form['descricao']
        cor = request.form['cor']
        tamanho = request.form['tamanho']
        imagem = request.files['imagem']

        if imagem:
            filename = secure_filename(imagem.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            imagem.save(image_path)

        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO produtos (descricao, foto_url)
            VALUES (?, ?)
        ''', (descricao, image_path))
        produto_id = cursor.lastrowid

        cursor.execute('''
            INSERT INTO variacoes (produto_id, cor, tamanho)
            VALUES (?, ?, ?)
        ''', (produto_id, cor, tamanho))
        conn.commit()
        conn.close()

        flash("Produto e variação cadastrados com sucesso!", "success")
        return redirect(url_for('cadastro_produtos'))

    return render_template('cadastro_produtos.html')


if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True, port=5000)
