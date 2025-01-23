import requests
from apscheduler.schedulers.background import BackgroundScheduler
import sqlite3
import csv
import os
from datetime import datetime
from flask import Flask

app = Flask(__name__)

# Função para consultar a Z-API periodicamente
def consultar_respostas_enquete():
    zapi_url = 'https://api.z-api.io/instances/3D0410602BEFB06E5DF6EEE17BD0D626/token/626967F563B18033A5E7FC55/messages'
    headers = {
        'Content-Type': 'application/json',
        'Client-Token': 'F213ae86745424112ad31bc17d95bb2adS'  # Substitua pelo seu Client-Token
    }

    try:
        # Corrija o método de requisição aqui, conforme necessário
        response = requests.post(zapi_url, headers=headers)  # Troque GET por POST se necessário
        response.raise_for_status()  # Lança uma exceção para códigos de status de erro HTTP

        mensagens = response.json()  # Tenta converter a resposta para JSON
        if not isinstance(mensagens, list):
            print("A resposta da API não é uma lista.")
            return

        for mensagem in mensagens:
            if isinstance(mensagem, dict) and mensagem.get('pollMessageId') and mensagem.get('pollVote'):
                numero_telefone = mensagem.get('phone')
                poll_message_id = mensagem.get('pollMessageId')
                votos = mensagem.get('pollVote')

                # Processar cada voto recebido
                for voto in votos:
                    try:
                        conn = sqlite3.connect('votacao.db')
                        cursor = conn.cursor()

                        # Tenta gravar o voto no banco de dados
                        cursor.execute('''
                            INSERT INTO votos (produto_variacao_id, numero_telefone, voto, comentario)
                            VALUES (?, ?, ?, ?)
                        ''', (None, numero_telefone, voto['name'], None))

                        conn.commit()
                        conn.close()
                        print(f"Votos recebidos de {numero_telefone} para a enquete {poll_message_id}.")

                    except Exception as db_error:
                        print(f"Erro ao gravar no banco de dados: {db_error}")
                        # Se der erro ao gravar no banco, gera um CSV na pasta C:\dados
                        gerar_csv(numero_telefone, poll_message_id, votos)

    except requests.exceptions.RequestException as e:
        print(f"Erro ao consultar respostas da Z-API: {e}")

# Função para gerar um arquivo CSV caso não consiga gravar no banco de dados
def gerar_csv(numero_telefone, poll_message_id, votos):
    # Define o caminho e o nome do arquivo CSV
    data_hora = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_path = os.path.join('C:\\dados', f'resultados_votacao_{data_hora}.csv')

    # Gera o CSV com os votos recebidos
    with open(csv_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Telefone', 'ID da Enquete', 'Voto'])  # Cabeçalhos do CSV
        for voto in votos:
            writer.writerow([numero_telefone, poll_message_id, voto['name']])

    print(f"Arquivo CSV gerado em {csv_path}")

# Agendar a consulta periódica usando APScheduler
scheduler = BackgroundScheduler()
scheduler.add_job(consultar_respostas_enquete, 'interval', minutes=1)  # Executa a cada 1 minuto
scheduler.start()

# Exemplo do Flask rodando com agendador
@app.route('/')
def index():
    return 'Sistema de Votação em Funcionamento!'

if __name__ == '__main__':
    app.run(debug=True)
