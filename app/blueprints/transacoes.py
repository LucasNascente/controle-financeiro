from flask import Blueprint, render_template, request, session, redirect, url_for
from app.db import get_db_connection

transacoes_bp = Blueprint('transacoes', __name__)


@transacoes_bp.route('/nova_transacao', methods=['GET', 'POST'])
def nova_transacao():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.index'))
    usuario_id = session['usuario_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM categorias WHERE usuario_id = %s", (usuario_id,))
        categorias = cursor.fetchall()
        cursor.execute("SELECT * FROM contas WHERE usuario_id = %s", (usuario_id,))
        contas = cursor.fetchall()

        if request.method == 'POST':
            descricao = request.form['descricao']
            tipo = request.form['tipo']
            categoria_id = request.form['categoria_id']
            conta_id = request.form['conta_id']
            data_transacao = request.form['data_transacao']

            try:
                valor = float(request.form['valor'].replace(',', '.'))
            except (ValueError, AttributeError):
                return render_template('nova_transacao.html', categorias=categorias, contas=contas,
                                       erro="Valor inválido. Use apenas números, ex: 150,00")

            if valor <= 0:
                return render_template('nova_transacao.html', categorias=categorias, contas=contas,
                                       erro="O valor precisa ser maior que zero.")

            cursor.execute("""
                INSERT INTO transacoes (usuario_id, categoria_id, conta_id, descricao, valor, tipo, data_transacao) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (usuario_id, categoria_id, conta_id, descricao, valor, tipo, data_transacao))
            conn.commit()
            return redirect(url_for('dashboard.dashboard'))
    finally:
        cursor.close()
        conn.close()
    return render_template('nova_transacao.html', categorias=categorias, contas=contas)


@transacoes_bp.route('/editar_transacao/<int:id>', methods=['GET', 'POST'])
def editar_transacao(id):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.index'))
    usuario_id = session['usuario_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM transacoes WHERE id = %s AND usuario_id = %s", (id, usuario_id))
        transacao = cursor.fetchone()
        if not transacao:
            return redirect(url_for('dashboard.dashboard'))
        cursor.execute("SELECT * FROM categorias WHERE usuario_id = %s", (usuario_id,))
        categorias = cursor.fetchall()
        cursor.execute("SELECT * FROM contas WHERE usuario_id = %s", (usuario_id,))
        contas = cursor.fetchall()

        if request.method == 'POST':
            descricao = request.form['descricao']
            tipo = request.form['tipo']
            categoria_id = request.form['categoria_id']
            conta_id = request.form['conta_id']
            data_transacao = request.form['data_transacao']

            # Mantém o que o usuário digitou na tela em caso de erro, em vez de reverter pro valor antigo
            transacao_reenvio = dict(transacao)
            transacao_reenvio.update({
                'descricao': descricao, 'tipo': tipo, 'categoria_id': int(categoria_id),
                'conta_id': int(conta_id), 'data_transacao': data_transacao, 'valor': request.form['valor']
            })

            try:
                valor = float(request.form['valor'].replace(',', '.'))
            except (ValueError, AttributeError):
                return render_template('editar_transacao.html', transacao=transacao_reenvio, categorias=categorias,
                                       contas=contas, erro="Valor inválido. Use apenas números, ex: 150,00")

            if valor <= 0:
                return render_template('editar_transacao.html', transacao=transacao_reenvio, categorias=categorias,
                                       contas=contas, erro="O valor precisa ser maior que zero.")

            cursor.execute("""
                UPDATE transacoes 
                SET descricao = %s, valor = %s, tipo = %s, categoria_id = %s, conta_id = %s, data_transacao = %s
                WHERE id = %s AND usuario_id = %s
            """, (descricao, valor, tipo, categoria_id, conta_id, data_transacao, id, usuario_id))
            conn.commit()
            return redirect(url_for('dashboard.dashboard'))
    finally:
        cursor.close()
        conn.close()
    return render_template('editar_transacao.html', transacao=transacao, categorias=categorias, contas=contas)


@transacoes_bp.route('/deletar_transacao/<int:id>', methods=['POST'])
def deletar_transacao(id):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM transacoes WHERE id = %s AND usuario_id = %s", (id, session['usuario_id']))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('dashboard.dashboard'))
