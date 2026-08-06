import os
import requests
from flask import Blueprint, render_template, request, session, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from itsdangerous import SignatureExpired, BadTimeSignature
from app.db import get_db_connection
from app.extensions import serializer

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard.dashboard'))
    return render_template('login.html')


@auth_bp.route('/login', methods=['POST'])
def login():
    email_digitado = request.form['email']
    senha_digitada = request.form['senha']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email_digitado,))
        usuario = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    if usuario and check_password_hash(usuario['senha'], senha_digitada):
        session['usuario_id'] = usuario['id']
        session['usuario_nome'] = usuario['nome']
        session['usuario_perfil'] = usuario['perfil']
        return redirect(url_for('dashboard.dashboard'))
    else:
        return render_template('login.html', erro="E-mail ou senha incorretos!")


# Rota de Cadastro de Novos Usuários
@auth_bp.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        if len(senha) < 6:
            return render_template('cadastro.html', erro="A senha precisa ter pelo menos 6 caracteres.")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
            usuario_existente = cursor.fetchone()

            if usuario_existente:
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
        finally:
            cursor.close()
            conn.close()

        return render_template('login.html', sucesso="Conta criada com sucesso! Faça seu login.")

    return render_template('cadastro.html')


def _enviar_email_recuperacao(destinatario, nome, link_redefinicao):
    """Envia o e-mail de recuperação de senha via API do Resend (HTTPS),
    em vez de SMTP direto — necessário porque o plano gratuito do Render
    bloqueia as portas de SMTP (25, 465, 587).

    RESEND_FROM_EMAIL pode ficar em branco enquanto você não tiver um
    domínio verificado no Resend: nesse caso, usamos o endereço de teste
    onboarding@resend.dev, que só consegue enviar para o e-mail da sua
    própria conta Resend (bom o bastante pra testar; depois de verificar
    um domínio, atualize essa variável no Render pra enviar a qualquer
    destinatário).
    """
    api_key = os.getenv('RESEND_API_KEY')
    remetente = os.getenv('RESEND_FROM_EMAIL', 'onboarding@resend.dev')

    corpo_texto = f"""Olá, {nome}!

Recebemos uma solicitação para redefinir a senha da sua conta no Controle Financeiro.

Para criar uma nova senha, clique no link abaixo:
{link_redefinicao}

Este link é válido por 30 minutos. Se você não solicitou a alteração de senha, pode ignorar esta mensagem.
"""

    resposta = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "from": f"Controle Financeiro <{remetente}>",
            "to": [destinatario],
            "subject": "Recuperação de Senha - Controle Financeiro",
            "text": corpo_texto,
        },
        timeout=10,  # nunca deixa a requisição pendurada por muito tempo
    )
    resposta.raise_for_status()  # levanta erro se o Resend recusar o envio


# --- ROTA SOLICITAR RECUPERAÇÃO DE SENHA (ENVIA E-MAIL) ---
@auth_bp.route('/esqueci-senha', methods=['GET', 'POST'])
def esqueci_senha():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        email = request.form['email']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
            usuario = cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

        if not usuario:
            return render_template('esqueci_senha.html', erro="E-mail não encontrado no sistema!")

        token = serializer.dumps(email, salt='recuperar-senha')
        link_redefinicao = url_for('auth.redefinir_senha_token', token=token, _external=True)

        try:
            _enviar_email_recuperacao(email, usuario['nome'], link_redefinicao)
            return render_template('esqueci_senha.html', sucesso="E-mail de recuperação enviado! Verifique sua caixa de entrada (ou spam).")
        except Exception as e:
            print("Erro ao enviar e-mail:", e)
            return render_template('esqueci_senha.html', erro="Erro ao enviar o e-mail. Tente novamente mais tarde.")

    return render_template('esqueci_senha.html')


# --- ROTA REDEFINIR SENHA VIA TOKEN ---
@auth_bp.route('/redefinir-senha/<token>', methods=['GET', 'POST'])
def redefinir_senha_token(token):
    if 'usuario_id' in session:
        return redirect(url_for('dashboard.dashboard'))

    try:
        email = serializer.loads(token, salt='recuperar-senha', max_age=1800)
    except SignatureExpired:
        return render_template('login.html', erro="O link de recuperação expirou! Solicite um novo.")
    except BadTimeSignature:
        return render_template('login.html', erro="Link de recuperação inválido!")

    if request.method == 'POST':
        nova_senha = request.form['nova_senha']

        if len(nova_senha) < 6:
            return render_template('redefinir_senha.html', token=token, erro="A senha precisa ter pelo menos 6 caracteres.")

        senha_hash = generate_password_hash(nova_senha)

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE usuarios SET senha = %s WHERE email = %s", (senha_hash, email))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

        return render_template('login.html', sucesso="Senha redefinida com sucesso! Faça seu login.")

    return render_template('redefinir_senha.html', token=token)


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.index'))
