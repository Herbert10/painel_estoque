from flask import Flask, render_template, request, redirect, url_for, session
import os

app = Flask(__name__)
app.secret_key = 'super_secret_key'

# Caminhos dos arquivos
USUARIOS_TXT = "usuarios.txt"
PRODUTOS_TXT = "produtos.txt"
VOTOS_TXT = "votos.txt"
UPLOAD_FOLDER = "static/uploads"

# Criando a pasta de uploads se não existir
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Função para carregar usuários do arquivo
def carregar_usuarios():
    if not os.path.exists(USUARIOS_TXT):
        return {}
    usuarios = {}
    with open(USUARIOS_TXT, "r") as file:
        for linha in file:
            email, senha, tipo = linha.strip().split(",")
            usuarios[email] = {"senha": senha, "tipo": tipo}
    return usuarios

# Função para carregar produtos
def carregar_produtos():
    if not os.path.exists(PRODUTOS_TXT):
        return []
    produtos = []
    with open(PRODUTOS_TXT, "r") as file:
        for linha in file:
            nome, cor, tamanho, imagem = linha.strip().split(",")
            produtos.append({"nome": nome, "cor": cor, "tamanho": tamanho, "imagem": imagem})
    return produtos

# Função para verificar se usuário já votou
def ja_votou(usuario, produto, cor):
    if not os.path.exists(VOTOS_TXT):
        return False
    with open(VOTOS_TXT, "r") as file:
        for linha in file:
            u, p, c, nota = linha.strip().split(",")
            if u == usuario and p == produto and c == cor:
                return True
    return False

# Rota de Login
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]
        usuarios = carregar_usuarios()
        if email in usuarios and usuarios[email]["senha"] == senha:
            session["usuario"] = email
            session["tipo"] = usuarios[email]["tipo"]
            return redirect(url_for("votacao" if usuarios[email]["tipo"] == "usuario" else "admin"))
        return render_template("login.html", mensagem="Credenciais inválidas")
    return render_template("login.html")

# Rota de Administração (Cadastro de Produtos)
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "usuario" not in session or session["tipo"] != "admin":
        return redirect(url_for("login"))
    if request.method == "POST":
        nome = request.form["nome"]
        cor = request.form["cor"]
        tamanho = request.form["tamanho"]
        imagem = request.files["imagem"]
        caminho_imagem = os.path.join(UPLOAD_FOLDER, imagem.filename)
        imagem.save(caminho_imagem)
        with open(PRODUTOS_TXT, "a") as file:
            file.write(f"{nome},{cor},{tamanho},{caminho_imagem}\n")
    return render_template("admin.html")

# Rota de Votação
@app.route("/votacao", methods=["GET", "POST"])
def votacao():
    if "usuario" not in session or session["tipo"] != "usuario":
        return redirect(url_for("login"))
    produtos = carregar_produtos()
    if request.method == "POST":
        produto = request.form["produto"]
        cor = request.form["cor"]
        nota = request.form["nota"]
        if not ja_votou(session["usuario"], produto, cor):
            with open(VOTOS_TXT, "a") as file:
                file.write(f"{session['usuario']},{produto},{cor},{nota}\n")
    return render_template("votacao.html", produtos=produtos)

if __name__ == "__main__":
    app.run(debug=True)
