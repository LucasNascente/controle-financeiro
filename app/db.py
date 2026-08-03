import os
import mysql.connector
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'controle_financeiro')
    )