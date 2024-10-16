from sqlalchemy import create_engine
import streamlit as st
import pandas as pd
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configurações do banco de dados
DATABASE_CONFIG = {
    'dbname': 'gerenciamento_tarefas1',
    'user': 'postgres',
    'password': 'Ermec6sello*',
    'host': 'localhost',
    'port': 5432
}

def leitura_de_dados():
    if 'dados' not in st.session_state:
        # Criar a string de conexão usando SQLAlchemy
        connection_string = f"postgresql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['dbname']}"
        engine = create_engine(connection_string)

        try:
            # Ler dados da tabela faturamento_controle
            query = 'SELECT * FROM faturamento_controle'
            df_vendas = pd.read_sql_query(query, engine)
            
            # Verificar se o DataFrame está vazio
            if df_vendas.empty:
                logger.error("A consulta SQL não retornou dados.")
                st.error("A consulta SQL não retornou dados.")
                return
            
            logger.info(f"Número de linhas retornadas: {len(df_vendas)}")

            # Normalizar os nomes das colunas
            df_vendas.columns = df_vendas.columns.str.strip().str.lower()
            logger.info(f"Nomes das colunas após normalização: {df_vendas.columns.tolist()}")

            # Criar DataFrames agrupados por 'nature' e 'gru' se existirem
            if 'nature' in df_vendas.columns and 'gru' in df_vendas.columns:
                df_nature = df_vendas.groupby('nature').size().reset_index(name='count')
                df_gru = df_vendas.groupby('gru').size().reset_index(name='count')
            else:
                logger.error("As colunas 'nature' e/ou 'gru' não foram encontradas nos dados.")
                st.error("As colunas 'nature' e/ou 'gru' não foram encontradas nos dados.")
                return

            dados = {
                'df_vendas': df_vendas,
                'df_nature': df_nature,
                'df_gru': df_gru
            }
            st.session_state['dados'] = dados
        except Exception as e:
            logger.error(f"Erro ao carregar dados do banco de dados: {e}")
            st.error("Erro ao carregar dados do banco de dados.")