from flask import Flask, render_template, jsonify
import fdb
import os
import requests
import threading
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

app = Flask(__name__)

# Conexão com banco Firebird
def get_firebird_connection():
    return fdb.connect(
        host=os.getenv("FIREBIRD_HOST"),
        port=int(os.getenv("FIREBIRD_PORT")),
        database=os.getenv("FIREBIRD_DATABASE"),
        user=os.getenv("FIREBIRD_USER"),
        password=os.getenv("FIREBIRD_PASSWORD"),
    )

# Consulta ao banco
def fetch_data():
    conn = get_firebird_connection()
    cursor = conn.cursor()

    query = """
        SELECT PV.STATUS_WORKFLOW, COUNT(PV.PEDIDOV) AS QUANTIDADE
        FROM PEDIDO_VENDA PV
        WHERE PV.EFETUADO = 'F'
        GROUP BY PV.STATUS_WORKFLOW;
    """
    cursor.execute(query)
    result = cursor.fetchall()
    conn.close()
    return {str(row[0]): row[1] for row in result}

# Função para enviar mensagem via WhatsApp usando Z-API
def enviar_mensagem_whatsapp(mensagem):
    url = "https://api.z-api.io/instances/3D0410602BEFB06E5DF6EEE17BD0D626/token/CC6CF6CE09DC42573B89209B/send-text"
    client_token = "F431d58e253c34be3844b4bc62bb831e6S"  # Substitua pelo Client-Token fornecido

    headers = {
        "Content-Type": "application/json",
        "Client-Token": client_token
    }

    payload = {
        "phone": "5511941445959",  # Substitua pelo número correto
        "message": mensagem
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print("Mensagem enviada com sucesso!")
        else:
            print(f"Erro ao enviar mensagem: {response.text}")
    except Exception as e:
        print(f"Erro na integração com Z-API: {e}")

# Controle de estado crítico já processado
estado_critico_cache = {}

# Verificação de estado crítico e envio de alertas em thread
def verificar_estado_critico_async(grouped_cards):
    def verificar_e_enviar():
        critical_states = [
            {
                "labels": ["Aguardando impressão prioritário", "Aguardando impressão"],
                "alert_message": "\u26A0 Atenção: Rotina de impressão em estado crítico com {total} pedidos aguardando impressão. \u26A0"
            },
            {
                "labels": ["Aguardando conferência prioritário", "Aguardando conferência"],
                "alert_message": "\u26A0 Atenção: Rotina de conferência em estado crítico com {total} pedidos aguardando conferência. \u26A0"
            },
            {
                "labels": ["Aguardando atribuição de separador prioritário", "Aguardando atribuição de separador"],
                "alert_message": "\u26A0 Atenção: Rotina de atribuição de separador em estado crítico com {total} pedidos aguardando separação. \u26A0"
            }
        ]

        for state in critical_states:
            # Calcular o total para o estado crítico
            total = sum(
                next((card["value"] for group, cards in grouped_cards.items() for card in cards if card["label"] == label), 0)
                for label in state["labels"]
            )

            # Verificar se já foi processado recentemente
            cache_key = "-".join(state["labels"])
            last_processed = estado_critico_cache.get(cache_key, {"last_sent": None, "last_total": 0})

            # Se já enviado recentemente (menos de 5 minutos atrás) e o total não mudou, não reenvie
            if last_processed["last_sent"] and datetime.now() - last_processed["last_sent"] < timedelta(minutes=5):
                if last_processed["last_total"] == total:
                    continue

            # Atualizar cache e enviar mensagem
            estado_critico_cache[cache_key] = {"last_sent": datetime.now(), "last_total": total}
            if total > 10:
                mensagem = state["alert_message"].format(total=total)
                enviar_mensagem_whatsapp(mensagem)

                # Aguardar 2 minutos e verificar novamente
                time.sleep(120)
                updated_total = sum(
                    next((card["value"] for group, cards in grouped_cards.items() for card in cards if card["label"] == label), 0)
                    for label in state["labels"]
                )
                if updated_total > 10:
                    estado_critico_cache[cache_key] = {"last_sent": datetime.now(), "last_total": updated_total}
                    enviar_mensagem_whatsapp(mensagem)

    # Iniciar a verificação em um thread separado
    thread = threading.Thread(target=verificar_e_enviar)
    thread.start()

@app.route("/")
def index():
    db_data = fetch_data()

    # Cards
    grouped_cards = {
        "Personalizado": [
            {"label": "Aguardando impressão personalizado", "status": "47", "filial": "2", "tipo_pedido": "13"}
        ],
        "Fluxo de Pedidos": [
            {"label": "Aguardando impressão prioritário", "status": "47", "filial": "2"},
            {"label": "Aguardando impressão", "status": "45", "filial": "2"},
            {"label": "Aguardando atribuição de separador prioritário", "status": "148", "filial": "2"},
            {"label": "Aguardando atribuição de separador", "status": "149", "filial": "2"},
            {"label": "Aguardando separação prioritário", "status": "30", "filial": "2"},
            {"label": "Aguardando separação", "status": "4", "filial": "2"},
            {"label": "Aguardando conferência prioritário", "status": "32", "filial": "2"},
            {"label": "Aguardando conferência", "status": "6", "filial": "2"},
        ],
        "Enviar para Zanzibar": [
            {"label": "Aguardando impressão agrupamento prioritário", "status": "156", "filial": "14"},
            {"label": "Aguardando impressão agrupamento", "status": "153", "filial": "14"},
            {"label": "Aguardando separação agrupamento prioritário", "status": "155", "filial": "14"},
            {"label": "Aguardando separação agrupamento", "status": "152", "filial": "14"},
        ],
        "Aguardando chegar da Zanzibar": [
            {"label": "Aguardando retorno agrupamento prioritário", "status": "157", "filial": "2"},
            {"label": "Aguardando retorno agrupamento", "status": "146", "filial": "2"},
        ],
    }

    # Atribuir valores pelos dados do banco
    for group, cards in grouped_cards.items():
        for card in cards:
            card["value"] = db_data.get(card["status"], 0)

    # Verificar estados críticos e enviar alertas de forma assíncrona
    verificar_estado_critico_async(grouped_cards)

    return render_template("index.html", grouped_cards=grouped_cards)

@app.route("/api/data")
def get_data():
    db_data = fetch_data()
    return jsonify(db_data)

if __name__ == "__main__":
    app.run(debug=True)
