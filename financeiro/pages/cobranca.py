import streamlit as st
import pandas as pd
import json
from datetime import datetime
import os

# Caminho para o arquivo JSON
CLIENTES_FILE = os.path.join(os.path.dirname(__file__), 'clientes_cobranca.json')

def load_clientes():
    if os.path.exists(CLIENTES_FILE):
        with open(CLIENTES_FILE, 'r') as file:
            return json.load(file)
    return []

def save_clientes(clientes):
    with open(CLIENTES_FILE, 'w') as file:
        json.dump(clientes, file, indent=4)

def main():
    st.title("Cobrança")

    # Criar abas
    tab1, tab2 = st.tabs(["Cadastro de Clientes", "Visualização de Clientes"])

    with tab1:
        st.header("Cadastro de Clientes para Cobrança")

        # Formulário de cadastro
        with st.form("cadastro_cliente"):
            codigo = st.text_input("Código do Cliente")
            nome = st.text_input("Nome do Cliente")
            responsavel = st.selectbox("Responsável", ["Gerente de Vendas", "Vendedor", "Presidente"])
            registrado_por = st.session_state.user['nome_completo'] if 'user' in st.session_state else ""

            submitted = st.form_submit_button("Cadastrar Cliente")

            if submitted:
                clientes = load_clientes()
                novo_cliente = {
                    "codigo": codigo,
                    "nome": nome,
                    "responsavel": responsavel,
                    "registrado_por": registrado_por,
                    "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                clientes.append(novo_cliente)
                save_clientes(clientes)
                st.success("Cliente cadastrado com sucesso!")

    with tab2:
        st.header("Clientes Cadastrados para Cobrança")

        clientes = load_clientes()
        if clientes:
            df = pd.DataFrame(clientes)
            st.dataframe(df)
        else:
            st.info("Nenhum cliente cadastrado ainda.")

if __name__ == "__main__":
    main()