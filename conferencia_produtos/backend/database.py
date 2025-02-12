import firebirdsql
import psycopg2
import redis
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env
load_dotenv()

# Conexão Firebird
def get_firebird_connection():
    return firebirdsql.connect(
        dsn=f"{os.getenv('FIREBIRD_HOST')}:{os.getenv('FIREBIRD_DB')}",
        user=os.getenv('FIREBIRD_USER'),
        password=os.getenv('FIREBIRD_PASSWORD')
    )

# Conexão PostgreSQL
def get_postgres_connection():
    return psycopg2.connect(
        dbname=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT')
    )

# Configuração do Redis
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    decode_responses=True
)
