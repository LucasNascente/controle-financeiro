from flask import Flask, render_template, request, session, redirect, url_for
from werkzeug.security import check_password_hash
from app.db import get_db_connection

app = Flask(__name__, template_folder='app/templates')
app.secret_key = 'chave_super_secreta_financeiro' 

# Rota Principal / Login
@app.route('/')
def index():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    email_digitado = request.form['email']
    senha_digitada = request.form['senha']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email_digitado,))
    usuario = cursor.fetchone()
    cursor.close()
    conn.close()

    if usuario and check_password_hash(usuario['senha'], senha_digitada):
        session['usuario_id'] = usuario['id']
        session['usuario_nome'] = usuario['nome']
        session['usuario_perfil'] = usuario['perfil']
        return redirect(url_for('dashboard'))
    else:
        return render_template('login.html', erro="E-mail ou senha incorretos!")

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
        
    usuario_id = session['usuario_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 1. Totais
    cursor.execute("""
        SELECT tipo, SUM(valor) as total 
        FROM transacoes 
        WHERE usuario_id = %s 
        GROUP BY tipo
    """, (usuario_id,))
    totais = cursor.fetchall()
    
    total_receitas = 0
    total_despesas = 0
    
    for t in totais:
        if t['tipo'] == 'receita':
            total_receitas = float(t['total'])
        elif t['tipo'] == 'despesa':
            total_despesas = float(t['total'])
            
    saldo_atual = total_receitas - total_despesas

    # 2. Despesas por Categoria (Gráfico)
    cursor.execute("""
        SELECT c.nome, c.cor, SUM(t.valor) as total
        FROM transacoes t
        JOIN categorias c ON t.categoria_id = c.id
        WHERE t.usuario_id = %s AND t.tipo = 'despesa'
        GROUP BY c.id
    """, (usuario_id,))
    despesas_categoria = cursor.fetchall()

    # 3. Busca todas as transações para a Tabela
    cursor.execute("""
        SELECT t.id, t.descricao, t.valor, t.tipo, DATE_FORMAT(t.data_transacao, '%d/%m/%Y') as data_f, c.nome as categoria
        FROM transacoes t
        JOIN categorias c ON t.categoria_id = c.id
        WHERE t.usuario_id = %s
        ORDER BY t.data_transacao DESC, t.id DESC
    """, (usuario_id,))
    lista_transacoes = cursor.fetchall()

    cursor.close()
    conn.close()
        
    return render_template('dashboard.html', 
                           receitas=total_receitas, 
                           despesas=total_despesas, 
                           saldo=saldo_atual,
                           grafico_categorias=despesas_categoria,
                           transacoes=lista_transacoes)

# Nova Transação
@app.route('/nova_transacao', methods=['GET', 'POST'])
def nova_transacao():
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
        
    usuario_id = session['usuario_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        descricao = request.form['descricao']
        valor = float(request.form['valor'].replace(',', '.'))
        tipo = request.form['tipo']
        categoria_id = request.form['categoria_id']
        conta_id = request.form['conta_id']
        data_transacao = request.form['data_transacao']
        
        cursor.execute("""
            INSERT INTO transacoes (usuario_id, categoria_id, conta_id, descricao, valor, tipo, data_transacao) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (usuario_id, categoria_id, conta_id, descricao, valor, tipo, data_transacao))
        conn.commit()
        
        cursor.close()
        conn.close()
        return redirect(url_for('dashboard'))
    
    cursor.execute("SELECT * FROM categorias WHERE usuario_id = %s", (usuario_id,))
    categorias = cursor.fetchall()
    
    cursor.execute("SELECT * FROM contas WHERE usuario_id = %s", (usuario_id,))
    contas = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('nova_transacao.html', categorias=categorias, contas=contas)

# Deletar Transação
@app.route('/deletar_transacao/<int:id>')
def deletar_transacao(id):
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transacoes WHERE id = %s AND usuario_id = %s", (id, session['usuario_id']))
    conn.commit()
    cursor.close()
    conn.close()
    
    return redirect(url_for('dashboard'))

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)