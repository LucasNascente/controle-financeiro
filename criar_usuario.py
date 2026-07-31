from werkzeug.security import generate_password_hash
from app.db import get_db_connection

# Conecta no banco
conn = get_db_connection()
cursor = conn.cursor()

# Dados do usuário de teste
email = 'admin@financeiro.com'
senha = '123'
senha_criptografada = generate_password_hash(senha)

# Verifica se o usuário já existe
cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
usuario = cursor.fetchone()

if usuario:
    # Se existir, apenas corrige a senha
    cursor.execute("UPDATE usuarios SET senha = %s WHERE email = %s", (senha_criptografada, email))
    print(f"Senha do usuário {email} atualizada com sucesso para: {senha}")
else:
    # Se não existir, cria do zero
    cursor.execute("INSERT INTO usuarios (nome, email, senha, perfil) VALUES (%s, %s, %s, %s)", 
                   ('Administrador', email, senha_criptografada, 'admin'))
    print(f"Usuário {email} criado com sucesso com a senha: {senha}")

conn.commit()
cursor.close()
conn.close()