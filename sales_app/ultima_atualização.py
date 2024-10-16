import psycopg2
from psycopg2 import sql

def verificar_ultima_atualizacao():
    try:
        # Conectar ao banco de dados
        conn = psycopg2.connect(
            dbname="faturamento",
            user="postgres",
            password="Ermec6sello*",
            host="localhost",
            port="5432"
        )
        cur = conn.cursor()
        
        # Consultar a última atualização
        cur.execute(sql.SQL("SELECT data_atualizacao FROM ultima_atualizacao ORDER BY data_atualizacao DESC LIMIT 1"))
        ultima_atualizacao = cur.fetchone()
        
        if ultima_atualizacao:
            print(f"Última atualização registrada no banco de dados: {ultima_atualizacao[0]}")
        else:
            print("Nenhuma atualização encontrada no banco de dados.")

    except Exception as e:
        print(f"Erro ao verificar atualização: {e}")
    finally:
        cur.close()
        conn.close()

verificar_ultima_atualizacao()