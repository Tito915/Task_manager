import pandas as pd

def validar_dataframe(df, required_columns):
    """
    Valida se o DataFrame contém as colunas necessárias e imprime informações úteis.

    :param df: DataFrame a ser validado
    :param required_columns: Lista de colunas que devem estar presentes no DataFrame
    :return: None
    """
    # Verificar se todas as colunas necessárias estão presentes
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"As seguintes colunas estão faltando no DataFrame: {missing_columns}")
    else:
        print("Todas as colunas necessárias estão presentes.")

    # Imprimir tipos de dados de cada coluna
    print("\nTipos de dados das colunas:")
    print(df.dtypes)

    # Imprimir as primeiras linhas do DataFrame para inspeção visual
    print("\nPrimeiras linhas do DataFrame:")
    print(df.head())

# Exemplo de uso
if __name__ == "__main__":
    # Criar um DataFrame de exemplo
    data = {
        'Ano': [2023, 2023, 2024],
        'Mês': [1, 2, 3],
        'Faturamento Mensal': [100000, 150000, 200000]
    }
    df_example = pd.DataFrame(data)
    df_example['Dia'] = 1  # Adiciona uma coluna 'Dia' com valor fixo 1

    # Tentar criar a coluna 'Data'
    try:
        # Usar pd.to_datetime com formato explícito
        df_example['Data'] = pd.to_datetime(df_example['Ano'].astype(str) + '-' + 
                                            df_example['Mês'].astype(str) + '-' + 
                                            df_example['Dia'].astype(str), format='%Y-%m-%d')
    except Exception as e:
        print(f"Erro ao criar coluna 'Data': {e}")

    # Validar o DataFrame
    validar_dataframe(df_example, ['Ano', 'Mês', 'Dia', 'Data', 'Faturamento Mensal'])