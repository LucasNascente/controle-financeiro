from flask import Blueprint, render_template, request, session, redirect, url_for
from app.db import get_db_connection

contas_bp = Blueprint('contas', __name__)


@contas_bp.route('/contas', methods=['GET', 'POST'])
def contas():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.index'))
    usuario_id = session['usuario_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if request.method == 'POST':
            nome = request.form['nome'].strip()
            if nome:
                cursor.execute("INSERT INTO contas (usuario_id, nome) VALUES (%s, %s)", (usuario_id, nome))
                conn.commit()
            return redirect(url_for('contas.contas'))

        cursor.execute("""
            SELECT c.id, c.nome, COUNT(t.id) as total_transacoes
            FROM contas c
            LEFT JOIN transacoes t ON t.conta_id = c.id
            WHERE c.usuario_id = %s
            GROUP BY c.id, c.nome
            ORDER BY c.nome ASC
        """, (usuario_id,))
        minhas_contas = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    return render_template('contas.html', contas=minhas_contas, erro=request.args.get('erro'))


@contas_bp.route('/deletar_conta/<int:id>', methods=['POST'])
def deletar_conta(id):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.index'))
    usuario_id = session['usuario_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT COUNT(*) as total FROM contas WHERE usuario_id = %s", (usuario_id,))
        total_contas = cursor.fetchone()['total']
        if total_contas <= 1:
            return redirect(url_for('contas.contas', erro="Você precisa manter pelo menos uma conta."))

        cursor.execute("SELECT COUNT(*) as total FROM transacoes WHERE conta_id = %s AND usuario_id = %s", (id, usuario_id))
        transacoes_vinculadas = cursor.fetchone()['total']
        if transacoes_vinculadas > 0:
            return redirect(url_for('contas.contas', erro="Essa conta tem transações vinculadas e não pode ser excluída."))

        cursor.execute("DELETE FROM contas WHERE id = %s AND usuario_id = %s", (id, usuario_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('contas.contas'))
