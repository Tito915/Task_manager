import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# Adicione o diretório onde firebase_utils.py está localizado ao sys.path
sys.path.append(str(Path("C:/Users/tito/OneDrive/Documentos/curso/pythoncurso/Gerenciamento_Tarefas")))

from firebase_utils import bucket, logger, baixar_arquivo

def carregar_dados():
    """Carrega os dados do arquivo Excel do Firebase Storage."""
    caminho_arquivo = 'SallesApp/Faturamento_total.xlsx'
    
    try:
        buffer = baixar_arquivo(caminho_arquivo)
        if buffer is None:
            logger.error("Não foi possível baixar o arquivo do Firebase.")
            return None
        
        df = pd.read_excel(buffer)
        df.columns = df.columns.str.strip().str.lower()
        df['data'] = pd.to_datetime(df['data'])
        df['gru'] = df['gru'].astype(str).str.strip()
        logger.info("Dados carregados com sucesso do Firebase.")
        return df
    except Exception as e:
        logger.error(f"Erro ao carregar dados: {e}")
        return None

def filtrar_faturamento_controle(df):
    """Filtra o DataFrame para excluir registros com GRU específicos."""
    return df[~df['gru'].isin(['21', '21.0', '021', '21,0'])]

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

    logger.info(f"Faturamento Bruto (Ano: {ano}, Mês: {mes}, Dia: {dia}, Vendedor: {vendedor}): R$ {faturamento_bruto:,.2f}")

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

    logger.info(f"Faturamento Líquido (Ano: {ano}, Mês: {mes}, Dia: {dia}, Vendedor: {vendedor}): R$ {faturamento_liquido:,.2f}")

    return faturamento_liquido

def obter_vendedores():
    """Obtém a lista de vendedores únicos do DataFrame."""
    df = carregar_dados()
    if df is None:
        return []

    if 'vendedor' not in df.columns:
        logger.error("Coluna 'vendedor' não encontrada no DataFrame.")
        return []

    vendedores = df['vendedor'].dropna().unique()
    vendedores = [v.strip() for v in vendedores if isinstance(v, str)]
    return sorted(set(vendedores))

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