from flask import Blueprint, render_template, request, session, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from app.db import get_db_connection

perfil_bp = Blueprint('perfil', __name__)


@perfil_bp.route('/perfil', methods=['GET', 'POST'])
def perfil():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.index'))

    usuario_id = session['usuario_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        if request.method == 'POST' and 'atualizar_dados' in request.form:
            novo_nome = request.form['nome']
            cursor.execute("UPDATE usuarios SET nome = %s WHERE id = %s", (novo_nome, usuario_id))
            conn.commit()
            session['usuario_nome'] = novo_nome
            return render_template('perfil.html',
                                   usuario={'nome': novo_nome, 'email': request.form['email_exibicao']},
                                   sucesso_dados="Nome atualizado com sucesso!")

        cursor.execute("SELECT id, nome, email FROM usuarios WHERE id = %s", (usuario_id,))
        usuario = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    return render_template('perfil.html', usuario=usuario)


@perfil_bp.route('/perfil/alterar-senha', methods=['POST'])
def alterar_senha_perfil():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.index'))

    usuario_id = session['usuario_id']
    senha_atual = request.form['senha_atual']
    nova_senha = request.form['nova_senha']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT senha, email, nome FROM usuarios WHERE id = %s", (usuario_id,))
        usuario = cursor.fetchone()

        if not check_password_hash(usuario['senha'], senha_atual):
            return render_template('perfil.html', usuario=usuario, erro_senha="A senha atual está incorreta!")

        if len(nova_senha) < 6:
            return render_template('perfil.html', usuario=usuario, erro_senha="A nova senha precisa ter pelo menos 6 caracteres.")

        nova_senha_hash = generate_password_hash(nova_senha)
        cursor.execute("UPDATE usuarios SET senha = %s WHERE id = %s", (nova_senha_hash, usuario_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return render_template('perfil.html', usuario=usuario, sucesso_senha="Senha alterada com sucesso!")


@perfil_bp.route('/perfil/excluir-conta', methods=['POST'])
def excluir_conta():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.index'))

    usuario_id = session['usuario_id']

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM transacoes WHERE usuario_id = %s", (usuario_id,))
        cursor.execute("DELETE FROM categorias WHERE usuario_id = %s", (usuario_id,))
        cursor.execute("DELETE FROM contas WHERE usuario_id = %s", (usuario_id,))
        cursor.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    session.clear()
    return redirect(url_for('auth.index'))
