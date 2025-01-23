from flask import Flask, request, render_template, redirect, url_for, flash, session
import pandas as pd
import os
import sqlite3
import logging

app = Flask(__name__)
app.secret_key = 'minha_chave_secreta'
UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
RESULTADO_PATH = r'C:\Dados\resultado.txt'

# Configuração de logging para depuração
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


# Função para verificar credenciais de login
def check_credentials(username, password, role):
    if role == 'MASTER':
        return username == 'MASTER' and password == 'MASTER'
    elif role == 'VENDEDOR':
        return username == 'VENDEDOR' and password == 'VENDEDOR'
    return False


# Função para inicializar o banco de dados
def inicializar_banco():
    try:
        conn = sqlite3.connect('produtos.db')
        cursor = conn.cursor()

        # Verificar se a coluna 'nome_usuario' já existe na tabela 'avaliacoes'
        cursor.execute("PRAGMA table_info(avaliacoes)")
        colunas = [coluna[1] for coluna in cursor.fetchall()]

        if 'nome_usuario' not in colunas:
            # Adicionar a coluna 'nome_usuario' à tabela 'avaliacoes' se não existir
            cursor.execute('ALTER TABLE avaliacoes ADD COLUMN nome_usuario TEXT')

        conn.commit()
        logging.info("Banco de dados inicializado com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao inicializar o banco de dados: {str(e)}")
    finally:
        conn.close()


# Função para carregar dados do Excel para o banco de dados SQLite
def carregar_dados_excel():
    try:
        caminho_arquivo = r'C:\Dados\PRODUTOS.xlsx'
        df = pd.read_excel(caminho_arquivo)

        conn = sqlite3.connect('produtos.db')
        cursor = conn.cursor()

        # Criar tabelas se não existirem
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cod_produto TEXT,
                descricao TEXT,
                cor TEXT,
                tamanho TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS imagens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto_id INTEGER,
                caminho_imagem TEXT,
                FOREIGN KEY (produto_id) REFERENCES produtos(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS avaliacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto_id INTEGER,
                cor TEXT,
                tamanho TEXT,
                nota INTEGER,
                observacao TEXT,
                nome_usuario TEXT,
                FOREIGN KEY (produto_id) REFERENCES produtos(id)
            )
        ''')

        # Limpar dados antigos
        cursor.execute('DELETE FROM produtos')
        cursor.execute('DELETE FROM imagens')
        cursor.execute('DELETE FROM avaliacoes')

        # Inserir dados na tabela produtos
        for _, row in df.iterrows():
            cursor.execute('''
                INSERT INTO produtos (cod_produto, descricao, cor, tamanho)
                VALUES (?, ?, ?, ?)
            ''', (row['COD_PRODUTO'], row['DESCRICAO'], row['COR'], row['TAMANHO']))

        conn.commit()
        logging.info("Dados carregados do Excel para o banco de dados.")
    except Exception as e:
        logging.error(f"Erro ao carregar dados do Excel: {str(e)}")
        flash(f"Erro ao carregar dados do Excel: {str(e)}")
    finally:
        conn.close()


# Inicializar banco de dados e carregar dados do Excel
inicializar_banco()
carregar_dados_excel()


# Rota para a página inicial
@app.route('/')
def index():
    logging.info("Página inicial carregada.")
    # Redirecionar para a tela de login
    return redirect(url_for('login', role='VENDEDOR'))


# Rota para a página de login (diferenciado por role)
@app.route('/login/<role>', methods=['GET', 'POST'])
def login(role):
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if check_credentials(username, password, role):
            session['role'] = role
            if role == 'MASTER':
                return redirect(url_for('master'))
            elif role == 'VENDEDOR':
                return redirect(url_for('seller'))
        else:
            flash('Credenciais inválidas. Tente novamente.')
            return redirect(url_for('login', role=role))
    return render_template('login.html', role=role)


# Rota para cadastro de produtos (tela do Master)
@app.route('/master', methods=['GET', 'POST'])
def master():
    if 'role' not in session or session['role'] != 'MASTER':
        return redirect(url_for('login', role='MASTER'))

    if request.method == 'POST':
        codigo_produto = request.form['product_code']
        arquivos = request.files.getlist('images')

        if not arquivos or codigo_produto == '':
            flash('Por favor, selecione um produto e faça upload de pelo menos uma imagem.')
            return redirect(url_for('master'))

        try:
            conn = sqlite3.connect('produtos.db')
            cursor = conn.cursor()

            for arquivo in arquivos:
                nome_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], arquivo.filename)
                arquivo.save(nome_arquivo)

                # Associar a imagem ao produto no banco de dados
                cursor.execute('''
                    INSERT INTO imagens (produto_id, caminho_imagem)
                    SELECT id, ? FROM produtos WHERE cod_produto = ?
                ''', (nome_arquivo, codigo_produto))

            conn.commit()
            flash('Imagens carregadas com sucesso!')
        except Exception as e:
            flash(f'Erro ao carregar as imagens: {str(e)}')
        finally:
            conn.close()
        return redirect(url_for('master'))

    # Recuperar lista de produtos para o formulário de seleção
    conn = sqlite3.connect('produtos.db')
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT cod_produto, descricao FROM produtos')
    produtos = cursor.fetchall()
    conn.close()

    return render_template('master.html', produtos=produtos)


# Rota para votação (tela do Vendedor)
@app.route('/seller', methods=['GET', 'POST'])
def seller():
    if 'role' not in session or session['role'] != 'VENDEDOR':
        return redirect(url_for('login', role='VENDEDOR'))

    conn = sqlite3.connect('produtos.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        try:
            nome_usuario = request.form['nome_usuario']
            observacao_produto = request.form.get('observacao_produto')

            # Verificar se o usuário forneceu o nome
            if not nome_usuario:
                flash('Por favor, forneça seu nome para finalizar a votação.')
                logging.warning("Nome do usuário não fornecido.")
                return redirect(url_for('seller'))

            # Processar os votos para cada combinação de cor e tamanho
            votos_salvos = False
            for produto_id in request.form.getlist('produto_id'):
                for key in request.form.keys():
                    if key.startswith(f'nota_{produto_id}_'):
                        _, pid, cor, tamanho = key.split('_')
                        nota = request.form[key]

                        # Salvar a avaliação no banco de dados
                        cursor.execute('''
                            INSERT INTO avaliacoes (produto_id, cor, tamanho, nota, observacao, nome_usuario)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (produto_id, cor, tamanho, nota, observacao_produto, nome_usuario))
                        votos_salvos = True

            if votos_salvos:
                conn.commit()
                logging.info("Avaliações salvas no banco de dados.")
                flash('Resultados salvos com sucesso!')
            else:
                flash('Nenhum voto foi registrado. Por favor, selecione uma nota.')
                logging.warning("Nenhum voto registrado.")

        except Exception as e:
            logging.error(f"Erro ao salvar a votação: {str(e)}")
            flash(f'Erro ao salvar a votação: {str(e)}')
        finally:
            conn.close()

        return redirect(url_for('seller'))

    # Recuperar produtos selecionados para votação, excluindo os que já foram avaliados
    cursor.execute('''
        SELECT p.cod_produto, p.descricao, GROUP_CONCAT(DISTINCT i.caminho_imagem), 
               GROUP_CONCAT(DISTINCT p.cor || '|' || p.tamanho)
        FROM produtos p
        INNER JOIN imagens i ON p.id = i.produto_id
        WHERE p.id NOT IN (SELECT DISTINCT produto_id FROM avaliacoes)
        GROUP BY p.cod_produto, p.descricao
    ''')
    produtos = cursor.fetchall()

    lista_produtos = []
    for produto in produtos:
        cod_produto, descricao, imagens, opcoes = produto
        opcoes_list = [tuple(ct.split('|')) for ct in set(opcoes.split(','))] if opcoes else []
        imagens_list = imagens.split(',') if imagens else []
        lista_produtos.append({
            'cod_produto': cod_produto,
            'descricao': descricao,
            'imagens': imagens_list,
            'opcoes': opcoes_list
        })

    conn.close()
    return render_template('seller.html', produtos=lista_produtos)


if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
