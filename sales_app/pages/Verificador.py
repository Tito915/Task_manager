import sys
from pathlib import Path

# Adicione o diretório raiz do projeto ao sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))

from utils import initialize_firebase, validar_conexao
import pandas as pd
from firebase_admin import storage
from datetime import datetime, timedelta
import io

def download_excel_from_firebase():
    initialize_firebase()
    
    if not validar_conexao():
        raise Exception("Não foi possível conectar ao Firebase")

    bucket = storage.bucket()
    blob = bucket.blob("SallesApp/Faturamento_total.xlsx")
    contents = blob.download_as_bytes()
    return pd.read_excel(io.BytesIO(contents))

def get_column_name(df, possible_names):
    for name in possible_names:
        if name.lower() in [col.lower().strip() for col in df.columns]:
            return df.columns[[col.lower().strip() for col in df.columns].index(name.lower())]
    raise KeyError(f"Nenhuma coluna encontrada para {possible_names}")

def calcular_receitas(mes=None, ano=None):
    df = download_excel_from_firebase()

    # Imprimir informações de debug
    print("Colunas no DataFrame:")
    print(df.columns)
    print("\nPrimeiras linhas do DataFrame:")
    print(df.head())

    # Mapear nomes de colunas
    col_data = get_column_name(df, ['data', 'DATA', 'Date'])
    col_valor = get_column_name(df, ['valor total liquido', 'Valor total Liquido', 'VALOR TOTAL LIQUIDO'])
    col_pedido = get_column_name(df, ['pedido', 'PEDIDO', 'Pedido'])

    # Converter a coluna de data para datetime e lidar com valores inválidos
    df[col_data] = pd.to_datetime(df[col_data], errors='coerce')

    # Remover linhas com datas inválidas ou valores nulos
    df = df.dropna(subset=[col_data, col_valor, col_pedido])

    # Converter coluna de valor para numérico
    df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce')

    # Remover linhas com valores não numéricos
    df = df.dropna(subset=[col_valor])

    # Obter a data atual
    data_atual = datetime.now()
    ano_atual = data_atual.year
    mes_atual = data_atual.month
    dia_atual = data_atual.day

    # Filtrar o DataFrame
    if mes and ano:
        df_filtrado = df[(df[col_data].dt.month == mes) & (df[col_data].dt.year == ano)]
    elif ano:
        df_filtrado = df[df[col_data].dt.year == ano]
    else:
        df_filtrado = df

    # Cálculos
    receita_anual = df[df[col_data].dt.year == ano_atual][col_valor].sum()
    receita_mensal = df[(df[col_data].dt.year == ano_atual) & (df[col_data].dt.month == mes_atual)][col_valor].sum()
    receita_diaria = df[df[col_data].dt.date == data_atual.date()][col_valor].sum()

    data_atual_no_ano_anterior = datetime(ano_atual - 1, mes_atual, dia_atual)
    receita_anterior = df[(df[col_data] >= datetime(ano_atual - 1, 1, 1)) & (df[col_data] <= data_atual_no_ano_anterior)][col_valor].sum()

    qtde_pedidos_atual = df[df[col_data].dt.year == ano_atual][col_pedido].nunique()
    qtde_pedidos_anterior = df[(df[col_data] >= datetime(ano_atual - 1, 1, 1)) & (df[col_data] <= data_atual_no_ano_anterior)][col_pedido].nunique()

    diferenca_receita = receita_anual - receita_anterior
    crescimento_receita = ((diferenca_receita / receita_anterior) * 100) if receita_anterior > 0 else float('inf')
    diferenca_pedidos = qtde_pedidos_atual - qtde_pedidos_anterior
    crescimento_pedidos = ((diferenca_pedidos / qtde_pedidos_anterior) * 100) if qtde_pedidos_anterior > 0 else float('inf')

    # Faturamento dos últimos 7 dias
    data_sete_dias_atras = data_atual - timedelta(days=7)
    faturamento_ultimos_sete_dias = df[df[col_data] >= data_sete_dias_atras].groupby(df[col_data].dt.date)[col_valor].sum().reset_index()
    faturamento_ultimos_sete_dias = [(data.strftime("%Y-%m-%d"), valor / 1000) for data, valor in zip(faturamento_ultimos_sete_dias[col_data], faturamento_ultimos_sete_dias[col_valor])]

    # Tickets por mês e ano
    tickets_por_mes_ano = df[df[col_valor] > 0].groupby([df[col_data].dt.year, df[col_data].dt.month]).agg({
        col_valor: ['max', 'mean', 'min']
    })
    tickets_por_mes_ano.columns = ['ticket_maximo', 'ticket_medio', 'ticket_minimo']
    tickets_por_mes_ano = tickets_por_mes_ano.reset_index()
    tickets_por_mes_ano.columns = ['ano', 'mes', 'ticket_maximo', 'ticket_medio', 'ticket_minimo']
    tickets_por_mes_ano = tickets_por_mes_ano.values.tolist()

    # Distribuição de clientes por faixa de valor
    def faixa_valor(valor):
        if 0 <= valor <= 100: return '0 a 100'
        elif 101 <= valor <= 300: return '101 a 300'
        elif 301 <= valor <= 500: return '301 a 500'
        elif 501 <= valor <= 1000: return '501 a 1.000'
        elif 1001 <= valor <= 2500: return '1.001 a 2.500'
        elif 2501 <= valor <= 5000: return '2.501 a 5.000'
        elif 5001 <= valor <= 10000: return '5.001 a 10.000'
        elif 10001 <= valor <= 25000: return '10.001 a 25.000'
        elif 25001 <= valor <= 50000: return '25.001 a 50.000'
        elif 50001 <= valor <= 84000: return '50.001 a 84.000'
        elif 84001 <= valor <= 100000: return '84.001 a 100.000'
        elif 100001 <= valor <= 168000: return '100.001 a 168.000'
        else: return 'Acima de 168.000'

    df_filtrado['faixa_valor'] = df_filtrado[col_valor].apply(faixa_valor)
    distribuicao_clientes = df_filtrado[df_filtrado[col_valor] > 0].groupby('faixa_valor')[col_pedido].nunique().reset_index()
    distribuicao_clientes = distribuicao_clientes.values.tolist()

    return (
        receita_anual, receita_mensal, receita_diaria, receita_anterior, diferenca_receita, crescimento_receita,
        qtde_pedidos_atual, qtde_pedidos_anterior, diferenca_pedidos, crescimento_pedidos,
        faturamento_ultimos_sete_dias, tickets_por_mes_ano, distribuicao_clientes
    )

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
        