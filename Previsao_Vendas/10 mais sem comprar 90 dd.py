import os
import psycopg2
import pandas as pd
import openai
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Carregar variáveis do .env
load_dotenv()

# Agora as variáveis estão disponíveis
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Configuração da API do OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)

def gerar_mensagem(chatgpt_prompt):
    """
    Função para gerar mensagens personalizadas usando a API do ChatGPT.
    """
    try:
        print(f"Enviando prompt para OpenAI: {chatgpt_prompt}")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": chatgpt_prompt}]
        )
        mensagem = response.choices[0].message.content.strip()
        print(f"Resposta gerada: {mensagem}")
        return mensagem
    except Exception as e:
        print(f"Erro ao gerar mensagem: {e}")
        return "Erro ao gerar mensagem"

# Conectar ao banco de dados
conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)
cursor = conn.cursor()

# Definir os períodos de compra
hoje = datetime.today()
limite_90_dias = hoje - timedelta(days=90)
limite_365_dias = hoje - timedelta(days=365)

# Consulta SQL para buscar os 10 melhores clientes PJ em faturamento com histórico de compras adequado
query = """
    SELECT c.cod_cliente, c.nome_cliente, c.vendedor_cadastro, MAX(v.data_movimento) as data_ultima_compra, 
           SUM(v.preco_total) as faturamento_total
    FROM megatoon.dclientes c
    JOIN megatoon.fvendas v ON c.id_cliente = v.id_cliente
    WHERE c.pf_pj = 'PJ'
      AND v.data_movimento BETWEEN %s AND %s
    GROUP BY c.cod_cliente, c.nome_cliente, c.vendedor_cadastro
    HAVING MAX(v.data_movimento) < %s
    ORDER BY faturamento_total DESC
    LIMIT 2
"""

cursor.execute(query, (limite_365_dias, hoje, limite_90_dias))
clientes = cursor.fetchall()

# Criar DataFrame
colunas = ["cod_cliente", "nome_cliente", "vendedor_cadastro", "data_ultima_compra", "faturamento_total"]
df = pd.DataFrame(clientes, columns=colunas)

# Gerar mensagens para e-mail e WhatsApp
mensagens_email = []
mensagens_whatsapp = []

for _, row in df.iterrows():
    nome = row["nome_cliente"]
    vendedor = row["vendedor_cadastro"]
    data_ultima_compra = row["data_ultima_compra"].strftime("%d/%m/%Y")

    # Criar mensagens personalizadas com IA
    prompt_email = f"""
    Gere uma mensagem formal para o cliente {nome}, mencionando que faz mais de 90 dias desde a última compra ({data_ultima_compra}), mas que ele esteve ativo no último ano. 
    Use tom amigável e incentive uma nova compra. Assine como {vendedor}.
    """
    mensagens_email.append(gerar_mensagem(prompt_email))

    prompt_whatsapp = f"""
    Gere uma mensagem curta e formal para WhatsApp para o cliente {nome}, mencionando que faz mais de 90 dias desde a última compra ({data_ultima_compra}), mas que ele esteve ativo no último ano. 
    Use tom amigável e incentive uma nova compra. Assine como {vendedor}.
    """
    mensagens_whatsapp.append(gerar_mensagem(prompt_whatsapp))

# Adicionar mensagens ao DataFrame
df["mensagem_email"] = mensagens_email
df["mensagem_whatsapp"] = mensagens_whatsapp

# Salvar em Excel
caminho_arquivo = r"C:\dados\clientes_inativos.xlsx"
df.to_excel(caminho_arquivo, index=False)

# Fechar conexão com banco
cursor.close()
conn.close()

print(f"Arquivo salvo em {caminho_arquivo}")
