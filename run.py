from flask import Flask, render_template, request, session, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from app.db import get_db_connection
import datetime

app = Flask(__name__, template_folder='app/templates')
app.secret_key = 'chave_super_secreta_financeiro' 

# --- CONFIGURAÇÕES DO FLASK-MAIL (GMAIL) ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'nascenteandrade@gmail.com'
app.config['MAIL_PASSWORD'] = 'xohepcqjwzzrslhu'  # Senha de App tratada sem espaços
app.config['MAIL_DEFAULT_SENDER'] = ('Controle Financeiro', 'nascenteandrade@gmail.com')

mail = Mail(app)
s = URLSafeTimedSerializer(app.secret_key)

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

# Rota de Cadastro de Novos Usuários
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        usuario_existente = cursor.fetchone()
        
        if usuario_existente:
            cursor.close()
            conn.close()
            return render_template('cadastro.html', erro="Este e-mail já está cadastrado!")
            
        senha_hash = generate_password_hash(senha)
        
        cursor.execute("""
            INSERT INTO usuarios (nome, email, senha, perfil) 
            VALUES (%s, %s, %s, %s)
        """, (nome, email, senha_hash, 'comum'))
        conn.commit()
        
        novo_id = cursor.lastrowid
        
        categorias_padrao = [
            ('Alimentação', '#ef4444'),
            ('Moradia', '#3b82f6'),
            ('Transporte', '#f59e0b'),
            ('Lazer', '#8b5cf6'),
            ('Salário / Receita', '#10b981')
        ]
        for cat_nome, cat_cor in categorias_padrao:
            cursor.execute("INSERT INTO categorias (usuario_id, nome, cor) VALUES (%s, %s, %s)", (novo_id, cat_nome, cat_cor))
            
        cursor.execute("INSERT INTO contas (usuario_id, nome) VALUES (%s, %s)", (novo_id, 'Carteira Principal'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return render_template('login.html', sucesso="Conta criada com sucesso! Faça seu login.")
        
    return render_template('cadastro.html')

# --- ROTA SOLICITAR RECUPERAÇÃO DE SENHA (ENVIA E-MAIL) ---
@app.route('/esqueci-senha', methods=['GET', 'POST'])
def esqueci_senha():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form['email']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        usuario = cursor.fetchone()
        cursor.close()
        conn.close()

        if not usuario:
            return render_template('esqueci_senha.html', erro="E-mail não encontrado no sistema!")

        # Gerar token criptografado
        token = s.dumps(email, salt='recuperar-senha')
        link_redefinicao = url_for('redefinir_senha_token', token=token, _external=True)

        try:
            msg = Message('Recuperação de Senha - Controle Financeiro', recipients=[email])
            msg.body = f"""Olá, {usuario['nome']}!

Recebemos uma solicitação para redefinir a senha da sua conta no Controle Financeiro.

Para criar uma nova senha, clique no link abaixo:
{link_redefinicao}

Este link é válido por 30 minutos. Se você não solicitou a alteração de senha, pode ignorar esta mensagem.
"""
            mail.send(msg)
            return render_template('esqueci_senha.html', sucesso="E-mail de recuperação enviado! Verifique sua caixa de entrada (ou spam).")
        except Exception as e:
            print("Erro ao enviar e-mail:", e)
            return render_template('esqueci_senha.html', erro="Erro ao enviar o e-mail. Tente novamente mais tarde.")

    return render_template('esqueci_senha.html')

# --- ROTA REDEFINIR SENHA VIA TOKEN ---
@app.route('/redefinir-senha/<token>', methods=['GET', 'POST'])
def redefinir_senha_token(token):
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))

    try:
        # Token é válido por 30 minutos (1800 segundos)
        email = s.loads(token, salt='recuperar-senha', max_age=1800)
    except SignatureExpired:
        return render_template('login.html', erro="O link de recuperação expirou! Solicite um novo.")
    except BadTimeSignature:
        return render_template('login.html', erro="Link de recuperação inválido!")

    if request.method == 'POST':
        nova_senha = request.form['nova_senha']
        senha_hash = generate_password_hash(nova_senha)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET senha = %s WHERE email = %s", (senha_hash, email))
        conn.commit()
        cursor.close()
        conn.close()

        return render_template('login.html', sucesso="Senha redefinida com sucesso! Faça seu login.")

    return render_template('redefinir_senha.html', token=token)

# --- DASHBOARD (Com filtro de Mês, Ano e Texto) ---
@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
        
    usuario_id = session['usuario_id']
    hoje = datetime.date.today()
    
    # Filtros recebidos via URL (GET)
    mes_selecionado = int(request.args.get('mes', hoje.month))
    ano_selecionado = int(request.args.get('ano', hoje.year))
    pesquisa = request.args.get('pesquisa', '') 

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Totais Receita/Despesa (Filtrado por mês/ano)
    cursor.execute("""
        SELECT tipo, SUM(valor) as total 
        FROM transacoes 
        WHERE usuario_id = %s AND MONTH(data_transacao) = %s AND YEAR(data_transacao) = %s
        GROUP BY tipo
    """, (usuario_id, mes_selecionado, ano_selecionado))
    totais = cursor.fetchall()
    
    total_receitas = 0.0
    total_despesas = 0.0
    
    for t in totais:
        if t['tipo'] == 'receita' and t['total'] is not None: 
            total_receitas = float(t['total'])
        elif t['tipo'] == 'despesa' and t['total'] is not None: 
            total_despesas = float(t['total'])
            
    saldo_atual = total_receitas - total_despesas

    # Gráfico (Apenas despesas)
    cursor.execute("""
        SELECT c.nome, c.cor, SUM(t.valor) as total
        FROM transacoes t
        JOIN categorias c ON t.categoria_id = c.id
        WHERE t.usuario_id = %s AND t.tipo = 'despesa' AND MONTH(t.data_transacao) = %s AND YEAR(t.data_transacao) = %s
        GROUP BY c.id, c.nome, c.cor
    """, (usuario_id, mes_selecionado, ano_selecionado))
    despesas_raw = cursor.fetchall()

    grafico_dados = []
    for d in despesas_raw:
        grafico_dados.append({
            'nome': str(d['nome']),
            'cor': str(d['cor']) if d['cor'] else '#2563eb',
            'total': float(d['total']) if d['total'] is not None else 0.0
        })

    # Tabela com filtro de pesquisa de texto
    query_transacoes = """
        SELECT t.id, t.descricao, t.valor, t.tipo, DATE_FORMAT(t.data_transacao, '%d/%m/%Y') as data_f, c.nome as categoria
        FROM transacoes t
        JOIN categorias c ON t.categoria_id = c.id
        WHERE t.usuario_id = %s AND MONTH(t.data_transacao) = %s AND YEAR(t.data_transacao) = %s
    """
    params = [usuario_id, mes_selecionado, ano_selecionado]

    # Se o usuário digitou algo na pesquisa, adicionamos ao filtro
    if pesquisa:
        query_transacoes += " AND t.descricao LIKE %s"
        params.append(f"%{pesquisa}%")

    query_transacoes += " ORDER BY t.data_transacao DESC, t.id DESC"
    
    cursor.execute(query_transacoes, params)
    lista_transacoes = cursor.fetchall()

    cursor.close()
    conn.close()
        
    return render_template('dashboard.html', 
                           receitas=total_receitas, 
                           despesas=total_despesas, 
                           saldo=saldo_atual,
                           grafico_categorias=grafico_dados,
                           transacoes=lista_transacoes,
                           mes_atual=mes_selecionado,
                           ano_atual=ano_selecionado)

# --- ROTAS DO PERFIL DO USUÁRIO ---
@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    if 'usuario_id' not in session:
        return redirect(url_for('index'))

    usuario_id = session['usuario_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST' and 'atualizar_dados' in request.form:
        novo_nome = request.form['nome']
        cursor.execute("UPDATE usuarios SET nome = %s WHERE id = %s", (novo_nome, usuario_id))
        conn.commit()
        session['usuario_nome'] = novo_nome  
        cursor.close()
        conn.close()
        return render_template('perfil.html', 
                               usuario={'nome': novo_nome, 'email': request.form['email_exibicao']}, 
                               sucesso_dados="Nome atualizado com sucesso!")

    cursor.execute("SELECT id, nome, email FROM usuarios WHERE id = %s", (usuario_id,))
    usuario = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('perfil.html', usuario=usuario)

@app.route('/perfil/alterar-senha', methods=['POST'])
def alterar_senha_perfil():
    if 'usuario_id' not in session:
        return redirect(url_for('index'))

    usuario_id = session['usuario_id']
    senha_atual = request.form['senha_atual']
    nova_senha = request.form['nova_senha']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT senha, email, nome FROM usuarios WHERE id = %s", (usuario_id,))
    usuario = cursor.fetchone()

    if not check_password_hash(usuario['senha'], senha_atual):
        cursor.close()
        conn.close()
        return render_template('perfil.html', usuario=usuario, erro_senha="A senha atual está incorreta!")

    nova_senha_hash = generate_password_hash(nova_senha)
    cursor.execute("UPDATE usuarios SET senha = %s WHERE id = %s", (nova_senha_hash, usuario_id))
    conn.commit()
    cursor.close()
    conn.close()

    return render_template('perfil.html', usuario=usuario, sucesso_senha="Senha alterada com sucesso!")

@app.route('/perfil/excluir-conta', methods=['POST'])
def excluir_conta():
    if 'usuario_id' not in session:
        return redirect(url_for('index'))

    usuario_id = session['usuario_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM transacoes WHERE usuario_id = %s", (usuario_id,))
    cursor.execute("DELETE FROM categorias WHERE usuario_id = %s", (usuario_id,))
    cursor.execute("DELETE FROM contas WHERE usuario_id = %s", (usuario_id,))
    cursor.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))

    conn.commit()
    cursor.close()
    conn.close()

    session.clear()
    return redirect(url_for('index'))

# --- ROTAS DE CATEGORIAS E TRANSAÇÕES ---
@app.route('/categorias', methods=['GET', 'POST'])
def categorias():
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
    usuario_id = session['usuario_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        nome = request.form['nome']
        cor = request.form['cor']
        cursor.execute("INSERT INTO categorias (usuario_id, nome, cor) VALUES (%s, %s, %s)", (usuario_id, nome, cor))
        conn.commit()
        return redirect(url_for('categorias'))
    cursor.execute("SELECT * FROM categorias WHERE usuario_id = %s ORDER BY nome ASC", (usuario_id,))
    minhas_categorias = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('categorias.html', categorias=minhas_categorias)

@app.route('/deletar_categoria/<int:id>')
def deletar_categoria(id):
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categorias WHERE id = %s AND usuario_id = %s", (id, session['usuario_id']))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('categorias'))

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
        return redirect(url_for('dashboard'))
    cursor.execute("SELECT * FROM categorias WHERE usuario_id = %s", (usuario_id,))
    categorias = cursor.fetchall()
    cursor.execute("SELECT * FROM contas WHERE usuario_id = %s", (usuario_id,))
    contas = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('nova_transacao.html', categorias=categorias, contas=contas)

@app.route('/editar_transacao/<int:id>', methods=['GET', 'POST'])
def editar_transacao(id):
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
            UPDATE transacoes 
            SET descricao = %s, valor = %s, tipo = %s, categoria_id = %s, conta_id = %s, data_transacao = %s
            WHERE id = %s AND usuario_id = %s
        """, (descricao, valor, tipo, categoria_id, conta_id, data_transacao, id, usuario_id))
        conn.commit()
        return redirect(url_for('dashboard'))
    cursor.execute("SELECT * FROM transacoes WHERE id = %s AND usuario_id = %s", (id, usuario_id))
    transacao = cursor.fetchone()
    if not transacao:
        return redirect(url_for('dashboard'))
    cursor.execute("SELECT * FROM categorias WHERE usuario_id = %s", (usuario_id,))
    categorias = cursor.fetchall()
    cursor.execute("SELECT * FROM contas WHERE usuario_id = %s", (usuario_id,))
    contas = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('editar_transacao.html', transacao=transacao, categorias=categorias, contas=contas)

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

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)