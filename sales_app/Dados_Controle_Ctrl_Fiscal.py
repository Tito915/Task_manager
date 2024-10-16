import pandas as pd
from datetime import datetime

# Caminho para o arquivo Excel
file_path = r'C:\Users\tito\OneDrive\Documentos\MBV\Madeireira\VENDAS\Power Bi\Fat_Ctrl\Faturamento_total.xlsx'
entrada_fiscal_path = r'C:\Users\tito\OneDrive\Documentos\MBV\Madeireira\Entrada\Entrada Fiscal.xlsx'

def carregar_dados_excel():
    """Carrega os dados do arquivo Excel."""
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip().str.lower()
        df['data'] = pd.to_datetime(df['data']).dt.date
        return df
    except Exception as e:
        print(f"Erro ao carregar dados: {e}")
        return None

def obter_faturamento_anual_todos():
    df = carregar_dados_excel()
    if df is None:
        return []
    # Aplicar o filtro para gru = "21" ou "21.0" ou "021"
    df_filtered = df[df['gru'].astype(str).isin(['21', '21.0', '021'])]
    faturamento_anual = df_filtered.groupby(df_filtered['data'].apply(lambda x: x.year))['valor total liquido'].sum()
    return [(int(ano), float(total)) for ano, total in faturamento_anual.items()]

def obter_faturamento_mensal_todos():
    df = carregar_dados_excel()
    if df is None:
        return []
    # Aplicar o filtro para gru = "21" ou "21.0" ou "021"
    df_filtered = df[df['gru'].astype(str).isin(['21', '21.0', '021'])]
    faturamento_mensal = df_filtered.groupby([df_filtered['data'].apply(lambda x: x.year), df_filtered['data'].apply(lambda x: x.month)])['valor total liquido'].sum()
    return [(int(ano), int(mes), float(total)) for (ano, mes), total in faturamento_mensal.items()]

def obter_faturamento_por_natureza(ano, mes):
    df = carregar_dados_excel()
    if df is None:
        return []
    # Aplicar o filtro para gru diferente de "21", "21.0" e "021"
    df_filtered = df[~df['gru'].astype(str).isin(['21', '21.0', '021'])]
    df_filtered = df_filtered[(df_filtered['data'].apply(lambda x: x.year) == ano) & (df_filtered['data'].apply(lambda x: x.month) == mes)]
    faturamento_por_natureza = df_filtered.groupby(df_filtered['nature'].str.strip().str.lower())['valor total liquido'].sum()
    return [(natureza, float(total)) for natureza, total in faturamento_por_natureza.items()]

def obter_entradas_mensais():
    """Carrega os dados de entrada de mercadorias por mês e ano."""
    try:
        df = pd.read_excel(entrada_fiscal_path)
        print(f"Colunas no arquivo: {df.columns}")  # Depuração
        df.columns = df.columns.str.strip().str.lower()
        print(f"Colunas após processamento: {df.columns}")  # Depuração
        
        if 'dt_nota' not in df.columns:
            print("Coluna 'dt_nota' não encontrada!")  # Depuração
            return []
        
        df['dt_nota'] = pd.to_datetime(df['dt_nota'], format='%d/%m/%y')
        print(f"Primeiras linhas de dt_nota: {df['dt_nota'].head()}")  # Depuração
        
        entradas_mensais = df.groupby([df['dt_nota'].dt.year, df['dt_nota'].dt.month])['total (#1)'].sum()
        print(f"Entradas mensais: {entradas_mensais}")  # Depuração
        
        return [(int(ano), int(mes), float(total)) for (ano, mes), total in entradas_mensais.items()]
    except Exception as e:
        print(f"Erro ao carregar dados de entrada: {e}")
        return []
    