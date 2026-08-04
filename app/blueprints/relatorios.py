import csv
import io
import datetime
from flask import Blueprint, render_template, request, session, redirect, url_for, Response
from app.db import get_db_connection
from app.queries import buscar_transacoes, calcular_totais

relatorios_bp = Blueprint('relatorios', __name__)


# --- ROTA DE EXTRATO (IMPRESSÃO / PDF) ---
@relatorios_bp.route('/extrato')
def extrato():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.index'))

    usuario_id = session['usuario_id']
    mes_selecionado = int(request.args.get('mes', 0))
    ano_selecionado = int(request.args.get('ano', 0))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT nome, email FROM usuarios WHERE id = %s", (usuario_id,))
        usuario = cursor.fetchone()

        transacoes = buscar_transacoes(cursor, usuario_id, mes_selecionado, ano_selecionado, ordem='ASC')
        total_receitas, total_despesas = calcular_totais(cursor, usuario_id, mes_selecionado, ano_selecionado)
    finally:
        cursor.close()
        conn.close()

    saldo = total_receitas - total_despesas

    meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    periodo = "Todos os Meses"
    if mes_selecionado > 0 and ano_selecionado > 0:
        periodo = f"{meses[mes_selecionado-1]} de {ano_selecionado}"

    data_atual = datetime.datetime.now().strftime('%d/%m/%Y às %H:%M')

    return render_template('extrato.html',
                           transacoes=transacoes,
                           receitas=total_receitas,
                           despesas=total_despesas,
                           saldo=saldo,
                           periodo=periodo,
                           usuario=usuario,
                           data_atual=data_atual)


# --- ROTA EXPORTAR PARA EXCEL (CSV) ---
@relatorios_bp.route('/exportar-excel')
def exportar_excel():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.index'))

    usuario_id = session['usuario_id']
    mes_selecionado = int(request.args.get('mes', 0))
    ano_selecionado = int(request.args.get('ano', 0))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        transacoes = buscar_transacoes(cursor, usuario_id, mes_selecionado, ano_selecionado, ordem='ASC')
    finally:
        cursor.close()
        conn.close()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')

    writer.writerow(['Data', 'Descricao', 'Categoria', 'Tipo', 'Valor (R$)'])

    for t in transacoes:
        valor_formatado = f"{t['valor']:.2f}".replace('.', ',')
        writer.writerow([t['data_f'], t['descricao'], t['categoria'], t['tipo'].capitalize(), valor_formatado])

    output.seek(0)
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=relatorio_financeiro.csv"}
    )
