"""
Funções de consulta de transações compartilhadas entre as rotas
/dashboard, /extrato e /exportar-excel, que antes repetiam a mesma
lógica de filtro por mês/ano/pesquisa em três lugares diferentes.
"""


def calcular_totais(cursor, usuario_id, mes=0, ano=0):
    """Retorna (total_receitas, total_despesas) do usuário no período informado.
    mes/ano = 0 significa 'todos'."""
    query = "SELECT tipo, SUM(valor) as total FROM transacoes WHERE usuario_id = %s"
    params = [usuario_id]

    if mes and mes > 0:
        query += " AND MONTH(data_transacao) = %s"
        params.append(mes)
    if ano and ano > 0:
        query += " AND YEAR(data_transacao) = %s"
        params.append(ano)

    query += " GROUP BY tipo"
    cursor.execute(query, params)

    receitas, despesas = 0.0, 0.0
    for row in cursor.fetchall():
        if row['tipo'] == 'receita' and row['total'] is not None:
            receitas = float(row['total'])
        elif row['tipo'] == 'despesa' and row['total'] is not None:
            despesas = float(row['total'])
    return receitas, despesas


def contar_transacoes(cursor, usuario_id, mes=0, ano=0, pesquisa=None):
    """Conta quantas transações batem com os filtros (usado para paginação)."""
    query = "SELECT COUNT(*) as total FROM transacoes t WHERE t.usuario_id = %s"
    params = [usuario_id]

    if mes and mes > 0:
        query += " AND MONTH(t.data_transacao) = %s"
        params.append(mes)
    if ano and ano > 0:
        query += " AND YEAR(t.data_transacao) = %s"
        params.append(ano)
    if pesquisa:
        query += " AND t.descricao LIKE %s"
        params.append(f"%{pesquisa}%")

    cursor.execute(query, params)
    return cursor.fetchone()['total']


def buscar_transacoes(cursor, usuario_id, mes=0, ano=0, pesquisa=None, ordem='DESC', limit=None, offset=0):
    """Busca as transações do usuário com os filtros de mês/ano/pesquisa em comum
    entre o dashboard, o extrato e a exportação CSV.

    ordem: 'DESC' ou 'ASC' (nunca vem de input do usuário, é sempre fixo no código
    que chama esta função — por isso é seguro concatenar direto na query).
    limit/offset: se limit for informado, pagina o resultado.
    """
    if ordem not in ('ASC', 'DESC'):
        ordem = 'DESC'

    query = f"""
        SELECT t.id, t.descricao, t.valor, t.tipo,
               DATE_FORMAT(t.data_transacao, '%d/%m/%Y') as data_f,
               c.nome as categoria, c.cor as categoria_cor
        FROM transacoes t
        JOIN categorias c ON t.categoria_id = c.id
        WHERE t.usuario_id = %s
    """
    params = [usuario_id]

    if mes and mes > 0:
        query += " AND MONTH(t.data_transacao) = %s"
        params.append(mes)
    if ano and ano > 0:
        query += " AND YEAR(t.data_transacao) = %s"
        params.append(ano)
    if pesquisa:
        query += " AND t.descricao LIKE %s"
        params.append(f"%{pesquisa}%")

    query += f" ORDER BY t.data_transacao {ordem}, t.id {ordem}"

    if limit is not None:
        query += " LIMIT %s OFFSET %s"
        params.append(limit)
        params.append(offset)

    cursor.execute(query, params)
    return cursor.fetchall()
