import psycopg2
from datetime import datetime, timedelta

def calcular_receitas(mes=None, ano=None):
    # Conexão com o banco de dados
    conn = psycopg2.connect(
        dbname="faturamento",
        user="postgres",
        password="Ermec6sello*",
        host="localhost",
        port="5432"
    )

    try:
        # Criar um cursor
        cur = conn.cursor()
        
        # Obter a data atual
        data_atual = datetime.now()
        ano_atual = data_atual.year
        mes_atual = data_atual.month
        dia_atual = data_atual.day
        
        # Receita Anual
        data_inicio_ano_atual = datetime(ano_atual, 1, 1)
        cur.execute("""
            SELECT SUM("valor total liquido") 
            FROM faturamento_controle 
            WHERE "data" >= %s AND "data" <= %s
        """, (data_inicio_ano_atual, data_atual))
        receita_anual = cur.fetchone()[0] or 0

        # Receita Mensal
        data_inicio_mes_atual = datetime(ano_atual, mes_atual, 1)
        cur.execute("""
            SELECT SUM("valor total liquido") 
            FROM faturamento_controle 
            WHERE "data" >= %s AND "data" <= %s
        """, (data_inicio_mes_atual, data_atual))
        receita_mensal = cur.fetchone()[0] or 0

        # Receita Diária
        cur.execute("""
            SELECT SUM("valor total liquido") 
            FROM faturamento_controle 
            WHERE "data" = %s
        """, (data_atual,))
        receita_diaria = cur.fetchone()[0] or 0

        # Consultar a receita do ano anterior até a mesma data
        data_atual_no_ano_anterior = datetime(ano_atual - 1, mes_atual, dia_atual)
        data_inicio_ano_anterior = datetime(ano_atual - 1, 1, 1)
        cur.execute("""
            SELECT SUM("valor total liquido") 
            FROM faturamento_controle 
            WHERE "data" >= %s AND "data" <= %s
        """, (data_inicio_ano_anterior, data_atual_no_ano_anterior))
        receita_anterior = cur.fetchone()[0] or 0

        # Consultar a contagem distinta de pedidos do ano atual até a data atual
        cur.execute("""
            SELECT COUNT(DISTINCT "pedido") 
            FROM faturamento_controle 
            WHERE "data" >= %s AND "data" <= %s
        """, (data_inicio_ano_atual, data_atual))
        qtde_pedidos_atual = cur.fetchone()[0] or 0

        # Consultar a contagem distinta de pedidos do ano anterior até a mesma data
        cur.execute("""
            SELECT COUNT(DISTINCT "pedido") 
            FROM faturamento_controle 
            WHERE "data" >= %s AND "data" <= %s
        """, (data_inicio_ano_anterior, data_atual_no_ano_anterior))
        qtde_pedidos_anterior = cur.fetchone()[0] or 0

        # Calcular o crescimento da receita
        diferenca_receita = receita_anual - receita_anterior
        crescimento_receita = ((diferenca_receita / receita_anterior) * 100) if receita_anterior > 0 else float('inf')

        # Calcular o crescimento dos pedidos
        diferenca_pedidos = qtde_pedidos_atual - qtde_pedidos_anterior
        crescimento_pedidos = ((diferenca_pedidos / qtde_pedidos_anterior) * 100) if qtde_pedidos_anterior > 0 else float('inf')

        # Calcular o faturamento dos últimos 7 dias
        data_sete_dias_atras = data_atual - timedelta(days=7)
        cur.execute("""
            SELECT "data", SUM("valor total liquido")
            FROM faturamento_controle
            WHERE "data" >= %s AND "data" <= %s
            GROUP BY "data"
            ORDER BY "data"
        """, (data_sete_dias_atras, data_atual))
        resultados_ultimos_sete_dias = cur.fetchall()

        # Criar uma lista para armazenar o faturamento dos últimos 7 dias
        faturamento_ultimos_sete_dias = [(data.strftime("%Y-%m-%d"), soma_valor / 1000) for data, soma_valor in resultados_ultimos_sete_dias]

        # Calcular o ticket máximo, médio e mínimo por mês e ano, considerando apenas valores positivos
        cur.execute("""
            SELECT 
                EXTRACT(YEAR FROM "data") AS ano,
                EXTRACT(MONTH FROM "data") AS mes,
                MAX("valor total liquido") AS ticket_maximo,
                AVG("valor total liquido") AS ticket_medio,
                MIN("valor total liquido") AS ticket_minimo
            FROM faturamento_controle
            WHERE "valor total liquido" > 0
            GROUP BY ano, mes
            ORDER BY ano, mes
        """)
        tickets_por_mes_ano = cur.fetchall()

        # Calcular a distribuição de clientes por faixa de valor de pedido
        query = """
            SELECT COUNT(DISTINCT "pedido"), 
                   CASE
                       WHEN "valor total liquido" BETWEEN 0 AND 100 THEN '0 a 100'
                       WHEN "valor total liquido" BETWEEN 101 AND 300 THEN '101 a 300'
                       WHEN "valor total liquido" BETWEEN 301 AND 500 THEN '301 a 500'
                       WHEN "valor total liquido" BETWEEN 501 AND 1000 THEN '501 a 1.000'
                       WHEN "valor total liquido" BETWEEN 1001 AND 2500 THEN '1.001 a 2.500'
                       WHEN "valor total liquido" BETWEEN 2501 AND 5000 THEN '2.501 a 5.000'
                       WHEN "valor total liquido" BETWEEN 5001 AND 10000 THEN '5.001 a 10.000'
                       WHEN "valor total liquido" BETWEEN 10001 AND 25000 THEN '10.001 a 25.000'
                       WHEN "valor total liquido" BETWEEN 25001 AND 50000 THEN '25.001 a 50.000'
                       WHEN "valor total liquido" BETWEEN 50001 AND 84000 THEN '50.001 a 84.000'
                       WHEN "valor total liquido" BETWEEN 84001 AND 100000 THEN '84.001 a 100.000'
                       WHEN "valor total liquido" BETWEEN 100001 AND 168000 THEN '100.001 a 168.000'
                       ELSE 'Acima de 168.000'
                   END AS faixa_valor
            FROM faturamento_controle
            WHERE "valor total liquido" > 0
        """
        # Aplicar filtros de mês e ano, se fornecidos
        if ano:
            query += f" AND EXTRACT(YEAR FROM \"data\") = {ano}"
        if mes:
            query += f" AND EXTRACT(MONTH FROM \"data\") = {mes}"
        
        query += " GROUP BY faixa_valor ORDER BY faixa_valor"
        
        cur.execute(query)
        distribuicao_clientes = cur.fetchall()

        # Retornar os resultados
        return (
            receita_anual, receita_mensal, receita_diaria, receita_anterior, diferenca_receita, crescimento_receita,
            qtde_pedidos_atual, qtde_pedidos_anterior, diferenca_pedidos, crescimento_pedidos,
            faturamento_ultimos_sete_dias, tickets_por_mes_ano, distribuicao_clientes
        )

    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    resultados = calcular_receitas()
    (receita_anual, receita_mensal, receita_diaria, receita_anterior, diferenca_receita, crescimento_receita, 
     qtde_pedidos_atual, qtde_pedidos_anterior, diferenca_pedidos, crescimento_pedidos, 
     faturamento_ultimos_sete_dias, tickets_por_mes_ano, distribuicao_clientes) = resultados

    print(f"Receita Anual: {receita_anual / 1_000_000:.2f} milhões")
    print(f"Receita Mensal: {receita_mensal / 1_000_000:.2f} milhões")
    print(f"Receita Diária: {receita_diaria / 1_000_000:.2f} milhões")
    print(f"Receita Anterior: {receita_anterior / 1_000_000:.2f} milhões")
    print(f"Crescimento da Receita: {diferenca_receita / 1_000_000:.2f} milhões {crescimento_receita:.2f}%")
    print(f"Pedidos Atuais: {qtde_pedidos_atual}")
    print(f"Pedidos Anteriores: {qtde_pedidos_anterior}")
    print(f"Crescimento dos Pedidos: {diferenca_pedidos} pedidos {crescimento_pedidos:.2f}%")
    print("Faturamento dos Últimos 7 Dias:")
    for data, faturamento in faturamento_ultimos_sete_dias:
        print(f"Data: {data}, Faturamento: {faturamento:.2f} mil")
    print("Tickets por Mês e Ano:")
    for ano, mes, ticket_maximo, ticket_medio, ticket_minimo in tickets_por_mes_ano:
        print(f"Ano: {int(ano)}, Mês: {int(mes)}, Máximo: {ticket_maximo:.2f}, Médio: {ticket_medio:.2f}, Mínimo: {ticket_minimo:.2f}")
    print("Distribuição de Clientes por Faixa de Valor:")
    for count, faixa in distribuicao_clientes:
        print(f"{faixa}: {count} clientes")