import psycopg2
import pyttsx3
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import openai
from openai import OpenAI
import pandas as pd  # Adicionado para manipulação de Excel

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configurações do banco de dados PostgreSQL
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Configurações da API da OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4"  # Ou "gpt-3.5-turbo" se preferir

# Inicializa o cliente da OpenAI
openai.api_key = OPENAI_API_KEY

# Inicializa o sintetizador de voz
sintetizador = pyttsx3.init()


# Configurar a voz para Microsoft Maria (Português do Brasil)
def configurar_voz():
    for voz in sintetizador.getProperty('voices'):
        if "Maria" in voz.name:
            sintetizador.setProperty('voice', voz.id)
            break
    sintetizador.setProperty('rate', 150)
    sintetizador.setProperty('volume', 1.0)


configurar_voz()

# Perguntas pré-definidas
PERGUNTAS_PRE_DEFINIDAS = {
    1: "Com base nas compras do cliente id_cliente=XXXXX, de quanto em quanto tempo ele compra?",
    2: "Qual a provável data da próxima compra do cliente id_cliente=XXXXX?",
    3: "Listar todos os clientes do vendedor_cadastro=XXXXX com a data da próxima compra."  # Nova pergunta pré-definida
}


# Função para conectar ao banco de dados
def conectar_banco():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None


# Função para executar uma consulta SQL
def executar_consulta(conn, sql):
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        resultado = cursor.fetchall()
        cursor.close()
        return resultado
    except Exception as e:
        print(f"Erro ao executar a consulta: {e}")
        return None


# Função para gerar SQL a partir de perguntas personalizadas
client = OpenAI()


def gerar_sql(pergunta):
    try:
        prompt = f"""
        Converta a pergunta abaixo em uma consulta SQL válida para PostgreSQL.
        Use apenas as tabelas do esquema 'megatoon':
        - Tabela 'megatoon.fvendas' contém os campos: id_cliente, data_movimento, quantidade, preco_total.
        - Tabela 'megatoon.dclientes' contém os campos: id_cliente, nome_cliente, cidade, estado, vendedor_cadastro.

        Pergunta: {pergunta}
        Apenas retorne a consulta SQL, sem explicações adicionais.
        """

        resposta = client.chat.completions.create(
            model="gpt-4",  # ou outro modelo que você deseja usar
            messages=[
                {"role": "system", "content": "Você é um assistente de banco de dados especializado em PostgreSQL."},
                {"role": "user", "content": prompt}
            ]
        )

        # Extrai apenas a consulta SQL da resposta
        sql = resposta.choices[0].message.content.strip()
        return sql
    except Exception as e:
        print(f"Erro ao gerar SQL: {e}")
        return None


# Função para gerar a consulta SQL do intervalo médio entre compras
def consulta_tempo_medio_compras(id_cliente):
    return f"""
    WITH diff_compras AS (
        SELECT 
            id_cliente, 
            EXTRACT(EPOCH FROM (data_movimento - LAG(data_movimento) OVER (
                PARTITION BY id_cliente ORDER BY data_movimento
            ))) / 86400 AS intervalo_dias
        FROM (
            SELECT DISTINCT id_cliente, data_movimento
            FROM megatoon.fvendas
            WHERE id_cliente = {id_cliente}
        ) subquery
    )
    SELECT 
        ROUND(AVG(intervalo_dias)) AS media_dias
    FROM diff_compras
    WHERE intervalo_dias IS NOT NULL
    GROUP BY id_cliente;
    """


# Função para gerar a consulta SQL da última compra
def consulta_ultima_compra(id_cliente):
    return f"""
    SELECT MAX(data_movimento)::DATE AS ultima_compra
    FROM megatoon.fvendas
    WHERE id_cliente = {id_cliente};
    """


# Função para calcular a próxima compra
def calcular_proxima_compra(ultima_compra, media_dias):
    try:
        ultima_compra_data = datetime.strptime(ultima_compra, "%Y-%m-%d")
        proxima_compra = ultima_compra_data + timedelta(days=media_dias)
        return proxima_compra.strftime("%Y-%m-%d")
    except Exception as e:
        return f"Erro ao calcular a próxima compra: {e}"


# Função para responder por áudio
def responder_por_voz(resposta):
    sintetizador.say(resposta)
    sintetizador.runAndWait()


# Função para selecionar uma pergunta pré-definida
def selecionar_pergunta():
    print("Selecione uma pergunta pré-definida:")
    for chave, pergunta in PERGUNTAS_PRE_DEFINIDAS.items():
        print(f"{chave}. {pergunta.replace('XXXXX', '[id_cliente ou vendedor_cadastro]')}")

    escolha = int(input("Digite o número da pergunta desejada: "))
    if escolha not in PERGUNTAS_PRE_DEFINIDAS:
        print("Opção inválida!")
        return None, None

    id_cliente_ou_vendedor = input("Digite o id_cliente ou vendedor_cadastro: ")
    if not id_cliente_ou_vendedor:
        print("ID ou vendedor inválido!")
        return None, None

    pergunta = PERGUNTAS_PRE_DEFINIDAS[escolha]
    return pergunta.replace("XXXXX", id_cliente_ou_vendedor), id_cliente_ou_vendedor


# Função para gerar o arquivo Excel com a lista de clientes e a data da próxima compra
def gerar_excel_clientes_vendedor(vendedor_cadastro, clientes):
    try:
        # Cria um DataFrame com os dados dos clientes
        df = pd.DataFrame(clientes, columns=[
            "cod_cliente",
            "id_cliente",
            "nome_cliente",
            "vendedor_cadastro",
            "proxima_compra",
            "ultima_compra",
            "intervalo_medio_compras"
        ])

        # Ordena o DataFrame pela data da próxima compra
        df = df.sort_values(by="proxima_compra")

        # Define o caminho do arquivo Excel
        caminho_arquivo = f"C:\\dados\\{vendedor_cadastro}.xlsx"

        # Salva o DataFrame em um arquivo Excel
        df.to_excel(caminho_arquivo, index=False)

        print(f"Arquivo Excel gerado com sucesso: {caminho_arquivo}")
    except Exception as e:
        print(f"Erro ao gerar o arquivo Excel: {e}")

# Função principal
def assistente():
    print("Olá! Sou seu assistente de banco de dados. Como posso ajudar?")
    responder_por_voz("Olá, mestre! Estou aqui para ajudar você com informações do banco de dados.")

    while True:
        print("\nEscolha:")
        print("1. Pergunta pré-definida")
        print("2. Pergunta personalizada")
        print("3. Sair")
        opcao = input("Digite sua escolha: ")

        if opcao == "1":
            pergunta, id_cliente_ou_vendedor = selecionar_pergunta()
            if not pergunta or not id_cliente_ou_vendedor:
                continue

            conn = conectar_banco()
            if conn:
                if "próxima compra" in pergunta and "vendedor_cadastro" not in pergunta:
                    resultado_ultima = executar_consulta(conn, consulta_ultima_compra(id_cliente_ou_vendedor))
                    if resultado_ultima and resultado_ultima[0][0]:
                        ultima_compra = str(resultado_ultima[0][0])
                        resultado_media = executar_consulta(conn, consulta_tempo_medio_compras(id_cliente_ou_vendedor))
                        if resultado_media and resultado_media[0][0]:
                            media_dias = int(resultado_media[0][0])
                            proxima_compra = calcular_proxima_compra(ultima_compra, media_dias)
                            print(f"Próxima compra estimada: {proxima_compra}")
                            responder_por_voz(f"A próxima compra está estimada para {proxima_compra}.")
                        else:
                            print("Não foi possível calcular a média de tempo entre compras.")
                    else:
                        print("Não foi possível encontrar a última compra.")
                    conn.close()
                elif "vendedor_cadastro" in pergunta:
                    # Consulta para obter os clientes do vendedor
                    sql_clientes_vendedor = f"""
                    SELECT id_cliente, nome_cliente, vendedor_cadastro
                    FROM megatoon.dclientes
                    WHERE vendedor_cadastro = '{id_cliente_ou_vendedor}';
                    """
                    resultado_clientes = executar_consulta(conn, sql_clientes_vendedor)
                    if resultado_clientes:
                        clientes_com_proxima_compra = []
                        for cliente in resultado_clientes:
                            id_cliente = cliente[0]
                            nome_cliente = cliente[1]
                            vendedor_cadastro = cliente[2]

                            # Obtém a última compra e a média de dias entre compras
                            resultado_ultima = executar_consulta(conn, consulta_ultima_compra(id_cliente))
                            if resultado_ultima and resultado_ultima[0][0]:
                                ultima_compra = str(resultado_ultima[0][0])
                                resultado_media = executar_consulta(conn, consulta_tempo_medio_compras(id_cliente))
                                if resultado_media and resultado_media[0][0]:
                                    media_dias = int(resultado_media[0][0])
                                    proxima_compra = calcular_proxima_compra(ultima_compra, media_dias)
                                    clientes_com_proxima_compra.append(
                                        (id_cliente, id_cliente, nome_cliente, vendedor_cadastro, proxima_compra,
                                         ultima_compra, media_dias)
                                    )
                                else:
                                    print(
                                        f"Não foi possível calcular a média de tempo entre compras para o cliente {id_cliente}.")
                            else:
                                print(f"Não foi possível encontrar a última compra para o cliente {id_cliente}.")

                        # Gera o arquivo Excel com a lista de clientes e a data da próxima compra
                        gerar_excel_clientes_vendedor(id_cliente_ou_vendedor, clientes_com_proxima_compra)
                    else:
                        print("Nenhum cliente encontrado para o vendedor informado.")
                else:
                    resultado = executar_consulta(conn, consulta_tempo_medio_compras(id_cliente_ou_vendedor))
                    conn.close()
                    if resultado:
                        resposta = f"O cliente faz compras a cada {resultado[0][0]} dias."
                        print(resposta)
                        responder_por_voz(resposta)
                    else:
                        print("Nenhum resultado encontrado.")
            else:
                print("Erro ao conectar ao banco de dados.")
        elif opcao == "2":
            pergunta = input("Digite sua pergunta personalizada: ")
            sql = gerar_sql(pergunta)
            if not sql:
                print("Não foi possível gerar a consulta SQL.")
                continue
            print(f"Consulta SQL gerada: {sql}")
            conn = conectar_banco()
            if conn:
                resultado = executar_consulta(conn, sql)
                conn.close()
                if resultado:
                    print(f"Resultado: {resultado}")
                    responder_por_voz(f"O resultado da consulta é: {resultado}.")
                else:
                    print("Nenhum resultado encontrado.")
        elif opcao == "3":
            responder_por_voz("Até logo, mestre!")
            break
        else:
            print("Opção inválida.")


# Executa o assistente
if __name__ == "__main__":
    assistente()