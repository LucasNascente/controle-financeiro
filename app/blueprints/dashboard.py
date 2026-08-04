import math
import datetime
from flask import Blueprint, render_template, request, session, redirect, url_for
from app.db import get_db_connection
from app.queries import buscar_transacoes, calcular_totais, contar_transacoes

dashboard_bp = Blueprint('dashboard', __name__)

TRANSACOES_POR_PAGINA = 15


@dashboard_bp.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.index'))

    usuario_id = session['usuario_id']
    hoje = datetime.date.today()

    mes_selecionado = int(request.args.get('mes', hoje.month))
    ano_selecionado = int(request.args.get('ano', hoje.year))
    pesquisa = request.args.get('pesquisa', '').strip()
    pagina_atual = max(1, int(request.args.get('pagina', 1) or 1))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # 1. Totais Receita/Despesa
        total_receitas, total_despesas = calcular_totais(cursor, usuario_id, mes_selecionado, ano_selecionado)
        saldo_atual = total_receitas - total_despesas

        # 2. Dados do Gráfico (Despesas por categoria)
        query_grafico = """
            SELECT c.nome, c.cor, SUM(t.valor) as total
            FROM transacoes t
            JOIN categorias c ON t.categoria_id = c.id
            WHERE t.usuario_id = %s AND t.tipo = 'despesa'
        """
        params_grafico = [usuario_id]

        if mes_selecionado > 0:
            query_grafico += " AND MONTH(t.data_transacao) = %s"
            params_grafico.append(mes_selecionado)

        if ano_selecionado > 0:
            query_grafico += " AND YEAR(t.data_transacao) = %s"
            params_grafico.append(ano_selecionado)

        query_grafico += " GROUP BY c.id, c.nome, c.cor"
        cursor.execute(query_grafico, params_grafico)
        despesas_raw = cursor.fetchall()

        grafico_dados = []
        for d in despesas_raw:
            grafico_dados.append({
                'nome': str(d['nome']),
                'cor': str(d['cor']) if d['cor'] else '#2563eb',
                'total': float(d['total']) if d['total'] is not None else 0.0
            })

        # 3. Tabela de Transações (paginada)
        total_transacoes = contar_transacoes(cursor, usuario_id, mes_selecionado, ano_selecionado, pesquisa)
        total_paginas = max(1, math.ceil(total_transacoes / TRANSACOES_POR_PAGINA))
        pagina_atual = min(pagina_atual, total_paginas)
        offset = (pagina_atual - 1) * TRANSACOES_POR_PAGINA

        lista_transacoes = buscar_transacoes(
            cursor, usuario_id, mes_selecionado, ano_selecionado, pesquisa,
            ordem='DESC', limit=TRANSACOES_POR_PAGINA, offset=offset
        )

    finally:
        cursor.close()
        conn.close()

    return render_template('dashboard.html',
                           receitas=total_receitas,
                           despesas=total_despesas,
                           saldo=saldo_atual,
                           grafico_categorias=grafico_dados,
                           transacoes=lista_transacoes,
                           mes_atual=mes_selecionado,
                           ano_atual=ano_selecionado,
                           pesquisa_atual=pesquisa,
                           pagina_atual=pagina_atual,
                           total_paginas=total_paginas,
                           total_transacoes=total_transacoes)
