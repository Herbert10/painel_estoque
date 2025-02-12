import os
import json
import smtplib
import requests
import psycopg2
import datetime
from flask import Flask, jsonify, request, render_template
from dotenv import load_dotenv
from decimal import Decimal
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText  # Adicionando a importação correta


# 🔹 Carregar as configurações do arquivo .env
load_dotenv()

app = Flask(__name__)

# 🔹 Configurações do Banco de Dados
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# 🔹 Configurações do Z-API (WhatsApp)
ZAPI_INSTANCE_ID = os.getenv("ZAPI_INSTANCE_ID")
ZAPI_CLIENT_TOKEN = os.getenv("ZAPI_CLIENT_TOKEN")
CLIENTE_TOKEN = os.getenv("CLIENTE_TOKEN")
ZAPI_URL_BASE = os.getenv("ZAPI_URL_BASE")

# 🔹 Configurações do E-mail (SMTP)
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_DESTINO = os.getenv("EMAIL_DESTINO")

# 🔹 Função para conectar ao banco PostgreSQL
def conectar_bd():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

# 🔹 Função para verificar se um dia é útil (sem feriado ou final de semana)
def verificar_dia_util(data):
    feriados = ["01-01", "25-12", "07-09", "15-11"]  # Adicione mais feriados conforme necessário
    dia_semana = data.weekday()  # 0 = Segunda, 6 = Domingo
    return dia_semana < 5 and data.strftime("%d-%m") not in feriados

# 🔹 Buscar clientes com títulos vencidos entre 5 e 10 dias
@app.route("/clientes_vencidos", methods=["GET"])
def buscar_clientes():
    conexao = conectar_bd()
    cursor = conexao.cursor()

    hoje = datetime.date.today()
    data_inicio = hoje - datetime.timedelta(days=10)  # Máximo 10 dias atrás
    data_fim = hoje - datetime.timedelta(days=5)  # Mínimo 5 dias atrás

    query = """
        SELECT f.lancamento, f.n_documento, f.gerador, f.valor_inicial, 
               c.nome_cliente, c.fone, f.data_vencimento
        FROM megatoon.flancamentos f
        JOIN megatoon.dclientes c ON f.gerador_origem = c.gerador
        WHERE f.data_vencimento BETWEEN %s AND %s 
        AND f.efetuado = 'F' 
        AND f.tipo = 'R'
        AND f.data_pagamento IS NULL 
        ORDER BY f.data_vencimento DESC;
    """

    cursor.execute(query, (data_inicio, data_fim))
    clientes = cursor.fetchall()

    resultado = []
    for cliente in clientes:
        valor = cliente[3] if cliente[3] is not None else 0.0  # Se `valor_inicial` for NULL, assume 0.0

        resultado.append({
            "lancamento": cliente[0],
            "n_documento": cliente[1],
            "gerador": cliente[2],
            "valor": float(valor),  # 🔹 Converte `Decimal` para `float`
            "nome_cliente": cliente[4],
            "telefone": cliente[5] if cliente[5] else "5511941445959",  # Se telefone for NULL, usa um padrão
            "data_vencimento": cliente[6].strftime("%d/%m/%Y")  # Formata a data para exibição
        })

    cursor.close()
    conexao.close()

    print("🔍 Clientes encontrados:", resultado)  # Debug no terminal

    return jsonify(resultado)

# 🔹 Enviar mensagens via WhatsApp usando Z-API
@app.route("/enviar_mensagem", methods=["POST"])
def enviar_mensagem():
    data = request.json
    clientes = data.get("clientes", [])

    if not clientes:
        return jsonify({"status": "Nenhum cliente selecionado."}), 400

    for cliente in clientes:
        telefone = cliente["telefone"]
        mensagem = (
            f"📢 *Aviso de Títulos Vencidos*\n\n"
            f"Olá, {cliente['nome_cliente']}! Identificamos que há títulos em aberto vencidos há mais de 5 dias.\n"
            f"🔹 *Título:* {cliente['n_documento']}\n"
            f"🔹 *Valor:* R$ {cliente['valor']:.2f}\n"
            f"🔹 *Vencimento:* {cliente['data_vencimento']}\n\n"
            "Pedimos a gentileza de regularizar o pagamento para evitar encargos. Caso já tenha efetuado, desconsidere esta mensagem."
        )

        url = f"{ZAPI_URL_BASE}/{ZAPI_INSTANCE_ID}/token/{ZAPI_CLIENT_TOKEN}/send-text"
        headers = {
            "Content-Type": "application/json",
            "Client-Token": CLIENTE_TOKEN
        }

        payload = {
            "phone": telefone,
            "message": mensagem
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            print(f"✅ Mensagem enviada com sucesso para {telefone}!")
        else:
            print(f"⚠️ Falha ao enviar mensagem para {telefone}: {response.text}")

    return jsonify({"status": "Mensagens enviadas com sucesso!"})

@app.route("/enviar_email", methods=["POST"])
def enviar_email():
    data = request.json
    clientes = data.get("clientes", [])

    if not clientes:
        return jsonify({"status": "Nenhum cliente selecionado."}), 400

    # Criar o conteúdo do e-mail
    assunto = "📢 Aviso de Títulos Vencidos"
    mensagem_html = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { padding: 10px; border-bottom: 1px solid #ddd; text-align: left; }
            th { background: #007BFF; color: white; }
        </style>
    </head>
    <body>
        <h2>📢 Aviso de Títulos Vencidos</h2>
        <p>Segue a lista de clientes com títulos vencidos há mais de 5 dias.</p>
        <table>
            <tr>
                <th>Nome do Cliente</th>
                <th>Título</th>
                <th>Valor</th>
                <th>Data de Vencimento</th>
            </tr>
    """

    for cliente in clientes:
        mensagem_html += f"""
        <tr>
            <td>{cliente['nome_cliente']}</td>
            <td>{cliente['n_documento']}</td>
            <td>R$ {cliente['valor']:.2f}</td>
            <td>{cliente['data_vencimento']}</td>
        </tr>
        """

    mensagem_html += """
        </table>
        <p>Por favor, regularize os pagamentos pendentes. Caso já tenha efetuado o pagamento, desconsidere esta mensagem.</p>
    </body>
    </html>
    """

    # Configurar o e-mail
    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = EMAIL_DESTINO
    msg["Subject"] = assunto
    msg.attach(MIMEText(mensagem_html, "html"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, EMAIL_DESTINO, msg.as_string())
        server.quit()
        print(f"✅ E-mail enviado com sucesso para {EMAIL_DESTINO}!")
        return jsonify({"status": "E-mail enviado com sucesso!"})
    except Exception as e:
        print(f"⚠️ Erro ao enviar e-mail: {e}")
        return jsonify({"status": "Erro ao enviar e-mail", "error": str(e)}), 500
# 🔹 Página inicial (carrega a interface HTML)
@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
