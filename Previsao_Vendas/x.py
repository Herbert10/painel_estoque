import os
from dotenv import load_dotenv

# Carrega as variáveis do .env
load_dotenv()

# Agora as variáveis estão disponíveis
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Verifica se as variáveis foram carregadas corretamente
print(f"DB_HOST: {DB_HOST}")
print(f"DB_PORT: {DB_PORT}")
print(f"DB_NAME: {DB_NAME}")
print(f"DB_USER: {DB_USER}")
print(f"DB_PASSWORD: {'*' * len(DB_PASSWORD) if DB_PASSWORD else 'Não carregado'}")
print(f"OPENAI_API_KEY: {'*' * len(OPENAI_API_KEY) if OPENAI_API_KEY else 'Não carregado'}")
