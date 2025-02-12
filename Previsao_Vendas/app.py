import os
import time
from dotenv import load_dotenv
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
from urllib.parse import quote
from prophet import Prophet
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# ⏳ Início do processamento
inicio_geral = time.time()

# 1️⃣ Carregar variáveis do arquivo .env
print("🔹 Carregando variáveis de ambiente...")
load_dotenv()

db_host = os.getenv("DB_HOST")
db_port = int(os.getenv("DB_PORT", 5432))
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")

# Codificar senha para evitar erro com caracteres especiais
password_encoded = quote(db_password)

# 2️⃣ Conectar ao PostgreSQL
print("🔹 Conectando ao banco de dados PostgreSQL...")
engine = create_engine(f'postgresql://{db_user}:{password_encoded}@{db_host}:{db_port}/{db_name}')


def extrair_dados():
    """ Extrai dados do banco de dados PostgreSQL """
    print("📥 Extraindo dados do banco...")

    vendas_query = """
    SELECT id_cliente, ptc, data_movimento, quantidade_vendida, faturamento_sem_frete
    FROM megatoon.fvendas
    WHERE cancelada = 'F';
    """
    clientes_query = """
    SELECT id_cliente, classificacao_cliente, cidade, estado, pf_pj, data_cadastro, desativado
    FROM megatoon.dclientes;
    """
    produtos_query = """
    SELECT ptc, categoria, colecao, grupo, tipo, faixa_valor, descricao_produto
    FROM megatoon.dprodutos;
    """

    inicio_extracao = time.time()
    df_vendas = pd.read_sql(vendas_query, engine)
    df_clientes = pd.read_sql(clientes_query, engine)
    df_produtos = pd.read_sql(produtos_query, engine)
    fim_extracao = time.time()

    print(f"✅ {len(df_vendas)} registros de vendas carregados.")
    print(f"✅ {len(df_clientes)} clientes carregados.")
    print(f"✅ {len(df_produtos)} produtos carregados.")
    print(f"⏳ Tempo de extração: {fim_extracao - inicio_extracao:.2f} segundos.")

    return df_vendas, df_clientes, df_produtos


# 3️⃣ Extrair os dados
df_vendas, df_clientes, df_produtos = extrair_dados()

# 4️⃣ Previsões com Prophet para todos os clientes (consolidado)
print("📊 Gerando previsões com Prophet para todos os clientes...")
inicio_prophet = time.time()

df_vendas['data_movimento'] = pd.to_datetime(df_vendas['data_movimento'])
df_vendas_agg = df_vendas.groupby(['data_movimento', 'id_cliente']).sum().reset_index()

# Criar DataFrame para salvar as previsões consolidadas
previsoes_prophet = []

# Loop para prever para cada cliente
for cliente_id in df_vendas['id_cliente'].unique():
    df_cliente = df_vendas_agg[df_vendas_agg['id_cliente'] == cliente_id]

    # 🛑 Verificar se o cliente tem registros suficientes (mínimo de 10 vendas)
    if len(df_cliente) < 10:
        print(f"⚠️ Cliente {cliente_id} tem apenas {len(df_cliente)} vendas. Pulando previsão.")
        previsoes_prophet.append(
            {'id_cliente': cliente_id, 'data_prevista': None, 'quantidade_prevista': 0, 'faturamento_previsto': 0})
        continue

    print(f"🔹 Processando previsões para o cliente {cliente_id} com {len(df_cliente)} vendas...")

    # Preparar dados para o Prophet
    df_cliente = df_cliente[['data_movimento', 'quantidade_vendida']].rename(
        columns={'data_movimento': 'ds', 'quantidade_vendida': 'y'})

    # Treinar o Prophet
    modelo_prophet = Prophet(yearly_seasonality=True)
    modelo_prophet.fit(df_cliente)

    # Fazer previsão para os próximos 6 meses
    futuro = modelo_prophet.make_future_dataframe(periods=6, freq='ME')  # Corrigido 'M' para 'ME'
    previsao = modelo_prophet.predict(futuro)

    # Selecionar apenas a data mais próxima do presente
    proxima_data = previsao[previsao['ds'] > pd.to_datetime('today')].head(1)

    if not proxima_data.empty:
        previsoes_prophet.append({
            'id_cliente': cliente_id,
            'data_prevista': proxima_data['ds'].values[0],  # Pegar a primeira data futura
            'quantidade_prevista': proxima_data['yhat'].values[0],
            'faturamento_previsto': proxima_data['yhat'].values[0] * df_cliente['y'].mean()  # Estimar faturamento
        })
    else:
        previsoes_prophet.append({
            'id_cliente': cliente_id,
            'data_prevista': None,
            'quantidade_prevista': 0,
            'faturamento_previsto': 0
        })

fim_prophet = time.time()
print(f"✅ Previsões geradas para todos os clientes. ⏳ Tempo total: {fim_prophet - inicio_prophet:.2f} segundos.")

# Converter resultados do Prophet para DataFrame consolidado
previsoes_prophet_df = pd.DataFrame(previsoes_prophet)

# 5️⃣ Salvando previsões no PostgreSQL
print("💾 Salvando previsões no banco...")
inicio_save = time.time()

previsoes_prophet_df.to_sql('previsao_vendas', engine, if_exists='replace', index=False, schema='megatoon')

fim_save = time.time()
print(f"✅ Previsões salvas no banco! ⏳ Tempo de salvamento: {fim_save - inicio_save:.2f} segundos.")

# ⏳ Tempo total de execução
fim_geral = time.time()
print(f"✅ 🚀 Processo finalizado! Tempo total: {fim_geral - inicio_geral:.2f} segundos.")
