import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import functools
import concurrent.futures

sys.path.append(str(Path("C:/Users/tito/OneDrive/Documentos/curso/pythoncurso/Gerenciamento_Tarefas")))

from firebase_utils import bucket, logger, baixar_arquivo

# Cache global para armazenar o DataFrame
_df_cache = None

@functools.lru_cache(maxsize=1)
def carregar_dados():
    """Carrega os dados do arquivo Excel do Firebase Storage com cache."""
    global _df_cache
    if _df_cache is not None:
        return _df_cache

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
        _df_cache = df
        logger.info("Dados carregados com sucesso do Firebase.")
        return df
    except Exception as e:
        logger.error(f"Erro ao carregar dados: {e}")
        return None

def filtrar_faturamento_controle(df):
    """Filtra o DataFrame para excluir registros com GRU específicos."""
    return df[~df['gru'].isin(['21', '21.0', '021', '21,0'])]

def calcular_faturamento(df, ano=None, mes=None, dia=None, vendedor=None, tipo='bruto'):
    """Calcula o Faturamento Bruto ou Líquido com base nos parâmetros."""
    df_filtrado = filtrar_faturamento_controle(df)

    if ano is not None:
        df_filtrado = df_filtrado[df_filtrado['data'].dt.year == ano]
    if mes is not None:
        df_filtrado = df_filtrado[df_filtrado['data'].dt.month == mes]
    if dia is not None:
        df_filtrado = df_filtrado[df_filtrado['data'].dt.day == dia]
    if vendedor is not None:
        df_filtrado = df_filtrado[df_filtrado['vendedor'] == vendedor]

    if tipo == 'bruto':
        faturamento = (df_filtrado['qtde'] * df_filtrado['valor']).sum()
    else:
        faturamento = df_filtrado['valor total liquido'].sum()

    return faturamento

def calcular_faturamento_bruto(ano=None, mes=None, dia=None, vendedor=None):
    df = carregar_dados()
    if df is None:
        return 0
    return calcular_faturamento(df, ano, mes, dia, vendedor, tipo='bruto')

def calcular_fld(ano=None, mes=None, dia=None, vendedor=None):
    df = carregar_dados()
    if df is None:
        return 0
    return calcular_faturamento(df, ano, mes, dia, vendedor, tipo='liquido')

@functools.lru_cache(maxsize=1)
def obter_vendedores():
    """Obtém a lista de vendedores únicos do DataFrame com cache."""
    df = carregar_dados()
    if df is None or 'vendedor' not in df.columns:
        return []
    vendedores = df['vendedor'].dropna().unique()
    return sorted(set(v.strip() for v in vendedores if isinstance(v, str)))

def obter_vendas_diarias(ano=None, mes=None, vendedores=None):
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
    return vendas_diarias.sort_values(['data', 'vendedor']).values.tolist()

def obter_maiores_faturamentos(ano=None, mes=None, limite=20):
    df = carregar_dados()
    if df is None:
        return []

    df_filtrado = filtrar_faturamento_controle(df)

    if ano is not None:
        df_filtrado = df_filtrado[df_filtrado['data'].dt.year == ano]
    if mes is not None:
        df_filtrado = df_filtrado[df_filtrado['data'].dt.month == mes]

    maiores_faturamentos = df_filtrado.groupby('razao')['valor total liquido'].sum().nlargest(limite)
    return list(maiores_faturamentos.items())

def carregar_dados_async():
    """Carrega os dados de forma assíncrona."""
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(carregar_dados)
        return future.result()

if __name__ == "__main__":
    # Carrega os dados de forma assíncrona
    df = carregar_dados_async()
    
    if df is not None:
        print("Dados carregados com sucesso.")
        print(f"Número total de registros: {len(df)}")
        
        # Executa as funções em paralelo
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(calcular_faturamento_bruto, ano=2024),
                executor.submit(calcular_fld, ano=2024),
                executor.submit(obter_vendedores),
                executor.submit(obter_vendas_diarias, ano=2024),
                executor.submit(obter_maiores_faturamentos, ano=2024)
            ]
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                print(f"Resultado: {result}")
    else:
        print("Falha ao carregar os dados.")