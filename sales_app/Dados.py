import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import logging

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuração do banco de dados PostgreSQL
db_url = 'postgresql+psycopg2://postgres:Ermec6sello*@localhost:5432/faturamento'
engine = create_engine(db_url)

# Caminho para o arquivo Excel
file_path = r'C:\Users\tito\OneDrive\Documentos\MBV\Madeireira\VENDAS\Power Bi\Fat_Ctrl\Faturamento_total.xlsx'

def atualizar_dados():
    try:
        # Ler dados do arquivo Excel
        df = pd.read_excel(file_path)

        # Remover espaços e converter nomes das colunas para minúsculas
        df.columns = df.columns.str.strip().str.lower()

        # Remover duplicatas
        df = df.drop_duplicates()

        # Atualizar dados na tabela faturamento_dados
        df.to_sql('faturamento_dados', con=engine, if_exists='replace', index=False)
        logging.info(f"Dados de faturamento atualizados com sucesso na tabela faturamento_dados. Total de linhas: {len(df)}")

        # Atualizar tabelas secundárias
        atualizar_tabelas_secundarias(engine)

        # Registrar última atualização
        registrar_ultima_atualizacao(engine)

        # Mensagem de confirmação
        logging.info(f"Dados atualizados com sucesso em: {datetime.now()}")

    except Exception as e:
        # Mensagem de erro
        logging.error(f"Erro ao atualizar os dados: {e}")

def atualizar_tabelas_secundarias(engine):
    with engine.connect() as connection:
        # Atualizar faturamento_controle
        connection.execute(text("DELETE FROM faturamento_controle;"))
        result_controle = connection.execute(text("""
            INSERT INTO faturamento_controle
            SELECT * FROM faturamento_dados WHERE gru NOT IN ('021', '21', '21.0');
        """))
        logging.info(f"Dados atualizados na tabela faturamento_controle. Total de linhas: {result_controle.rowcount}")

        # Atualizar faturamento_fiscal
        connection.execute(text("DELETE FROM faturamento_fiscal;"))
        result_fiscal = connection.execute(text("""
            INSERT INTO faturamento_fiscal
            SELECT * FROM faturamento_dados WHERE gru IN ('021', '21', '21.0');
        """))
        logging.info(f"Dados atualizados na tabela faturamento_fiscal. Total de linhas: {result_fiscal.rowcount}")

def registrar_ultima_atualizacao(engine):
    with engine.connect() as connection:
        connection.execute(text("INSERT INTO ultima_atualizacao (data_atualizacao) VALUES (NOW())"))
        logging.info("Data de última atualização registrada com sucesso.")

def verificar_dados_no_banco(engine):
    with engine.connect() as connection:
        # Verificar contagem de linhas na tabela faturamento_dados
        result_dados = connection.execute(text("SELECT COUNT(*) FROM faturamento_dados"))
        count_dados = result_dados.scalar()
        logging.info(f"Total de linhas na tabela faturamento_dados: {count_dados}")

        # Verificar contagem de linhas na tabela faturamento_controle
        result_controle = connection.execute(text("SELECT COUNT(*) FROM faturamento_controle"))
        count_controle = result_controle.scalar()
        logging.info(f"Total de linhas na tabela faturamento_controle: {count_controle}")

        # Verificar contagem de linhas na tabela faturamento_fiscal
        result_fiscal = connection.execute(text("SELECT COUNT(*) FROM faturamento_fiscal"))
        count_fiscal = result_fiscal.scalar()
        logging.info(f"Total de linhas na tabela faturamento_fiscal: {count_fiscal}")

        # Verificar a última atualização registrada
        result_ultima_atualizacao = connection.execute(text("SELECT data_atualizacao FROM ultima_atualizacao ORDER BY data_atualizacao DESC LIMIT 1"))
        ultima_atualizacao = result_ultima_atualizacao.scalar()
        logging.info(f"Última atualização registrada: {ultima_atualizacao}")

if __name__ == "__main__":
    atualizar_dados()
    verificar_dados_no_banco(engine)