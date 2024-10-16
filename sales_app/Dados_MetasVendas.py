import pandas as pd
from datetime import datetime

# Caminho para o arquivo Excel
EXCEL_PATH = r'C:\Users\tito\OneDrive\Documentos\MBV\Madeireira\VENDAS\Power Bi\Fat_Ctrl\Faturamento_total.xlsx'

def carregar_dados():
    """Carrega os dados do arquivo Excel."""
    try:
        df = pd.read_excel(EXCEL_PATH)
        df.columns = df.columns.str.strip().str.lower()
        df['data'] = pd.to_datetime(df['data'])
        df['gru'] = df['gru'].astype(str).str.strip()
        return df
    except Exception as e:
        print(f"Erro ao carregar dados: {e}")
        return None

def filtrar_faturamento_controle(df):
    """Filtra o DataFrame para excluir registros com GRU específicos."""
    return df[~df['gru'].isin(['21', '21.0', '021', '21,0'])]

# O resto das funções permanece o mesmo

def calcular_faturamento_bruto(ano=None, mes=None, dia=None, vendedor=None):
    """Calcula o Faturamento Bruto para o ano/mês/dia/vendedor especificado usando qtde e valor."""
    df = carregar_dados()
    if df is None:
        return 0

    df_filtrado = filtrar_faturamento_controle(df)

    if ano is not None:
        df_filtrado = df_filtrado[df_filtrado['data'].dt.year == ano]
    if mes is not None:
        df_filtrado = df_filtrado[df_filtrado['data'].dt.month == mes]
    if dia is not None:
        df_filtrado = df_filtrado[df_filtrado['data'].dt.day == dia]
    if vendedor is not None:
        df_filtrado = df_filtrado[df_filtrado['vendedor'] == vendedor]

    faturamento_bruto = (df_filtrado['qtde'] * df_filtrado['valor']).sum()

    print(f"Faturamento Bruto (Ano: {ano}, Mês: {mes}, Dia: {dia}, Vendedor: {vendedor}): R$ {faturamento_bruto:,.2f}")

    return faturamento_bruto

def calcular_fld(ano=None, mes=None, dia=None, vendedor=None):
    """Calcula o Faturamento Líquido para o ano/mês/dia/vendedor especificado usando valor total liquido."""
    df = carregar_dados()
    if df is None:
        return 0

    df_filtrado = filtrar_faturamento_controle(df)

    if ano is not None:
        df_filtrado = df_filtrado[df_filtrado['data'].dt.year == ano]
    if mes is not None:
        df_filtrado = df_filtrado[df_filtrado['data'].dt.month == mes]
    if dia is not None:
        df_filtrado = df_filtrado[df_filtrado['data'].dt.day == dia]
    if vendedor is not None:
        df_filtrado = df_filtrado[df_filtrado['vendedor'] == vendedor]

    faturamento_liquido = df_filtrado['valor total liquido'].sum()

    print(f"Faturamento Líquido (Ano: {ano}, Mês: {mes}, Dia: {dia}, Vendedor: {vendedor}): R$ {faturamento_liquido:,.2f}")

    return faturamento_liquido

def obter_vendedores():
    """Obtém a lista de vendedores únicos do DataFrame."""
    df = carregar_dados()
    if df is None:
        return []

    # Certifique-se de que a coluna 'vendedor' existe
    if 'vendedor' not in df.columns:
        print("Coluna 'vendedor' não encontrada no DataFrame.")
        return []

    # Obter vendedores únicos, removendo valores nulos ou vazios
    vendedores = df['vendedor'].dropna().unique()
    
    # Converter para lista e remover espaços em branco
    vendedores = [v.strip() for v in vendedores if isinstance(v, str)]
    
    return sorted(set(vendedores))  # Remover duplicatas e ordenar

def obter_vendas_diarias(ano=None, mes=None, vendedores=None):
    """Obtém vendas diárias para o ano/mês/vendedores especificados."""
    df = carregar_dados()
    if df is None:
        return []

    df_filtrado = filtrar_faturamento_controle(df)

    if ano is not None:
        df_filtrado = df_filtrado[df_filtrado['data'].dt.year == ano]
    if mes is not None:
        df_filtrado = df_filtrado[df_filtrado['data'].dt.month == mes]
    if vendedores:
        df_filtrado = df_filtrado[df_filtrado['vendedor'].isin(vendedores)]

    vendas_diarias = df_filtrado.groupby(['data', 'vendedor']).apply(lambda x: (x['qtde'] * x['valor']).sum()).reset_index()
    vendas_diarias.columns = ['data', 'vendedor', 'vendas_diarias']
    vendas_diarias = vendas_diarias.sort_values(['data', 'vendedor'])

    return vendas_diarias.values.tolist()

def obter_maiores_faturamentos(ano=None, mes=None, limite=20):
    """Obtém os maiores faturamentos de clientes para o ano/mês especificado."""
    df = carregar_dados()
    if df is None:
        return []

    df_filtrado = filtrar_faturamento_controle(df)

    if ano is not None:
        df_filtrado = df_filtrado[df_filtrado['data'].dt.year == ano]
    if mes is not None:
        df_filtrado = df_filtrado[df_filtrado['data'].dt.month == mes]

    maiores_faturamentos = df_filtrado.groupby('razao')['valor total liquido'].sum().sort_values(ascending=False).head(limite)
    
    return list(maiores_faturamentos.items())