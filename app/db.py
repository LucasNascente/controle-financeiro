import mysql.connector

def get_db_connection():
    # Cria e retorna a conexão com o banco do XAMPP
    connection = mysql.connector.connect(
        host='127.0.0.1',           
        port=3306,                  
        user='root',                
        password='ceub123456',  
        database='controle_financeiro'
    )
    return connection