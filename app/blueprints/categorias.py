from flask import Blueprint, render_template, request, session, redirect, url_for
from app.db import get_db_connection

categorias_bp = Blueprint('categorias', __name__)


@categorias_bp.route('/categorias', methods=['GET', 'POST'])
def categorias():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.index'))
    usuario_id = session['usuario_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if request.method == 'POST':
            nome = request.form['nome']
            cor = request.form['cor']
            cursor.execute("INSERT INTO categorias (usuario_id, nome, cor) VALUES (%s, %s, %s)", (usuario_id, nome, cor))
            conn.commit()
            return redirect(url_for('categorias.categorias'))
        cursor.execute("SELECT * FROM categorias WHERE usuario_id = %s ORDER BY nome ASC", (usuario_id,))
        minhas_categorias = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    return render_template('categorias.html', categorias=minhas_categorias)


@categorias_bp.route('/deletar_categoria/<int:id>', methods=['POST'])
def deletar_categoria(id):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM categorias WHERE id = %s AND usuario_id = %s", (id, session['usuario_id']))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('categorias.categorias'))
