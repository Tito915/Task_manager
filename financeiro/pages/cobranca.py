import streamlit as st
import pandas as pd
import json
from datetime import datetime
import os
import firebase_admin
from firebase_admin import credentials, storage
import io

# Inicialização do Firebase (certifique-se de que isso seja feito apenas uma vez)
if not firebase_admin._apps:
    cred = credentials.Certificate("caminho/para/seu/arquivo/de/credenciais.json")
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'gerenciador-de-tarefas-mbv.appspot.com'
    })


# Caminhos para os arquivos JSON
CLIENTES_FILE = os.path.join(os.path.dirname(__file__), 'clientes_cobranca.json')
LOG_FILE = os.path.join(os.path.dirname(__file__), 'log_cobranca.json')

def load_data(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return []

def save_data(data, file_path):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def add_log(action, details, user):
    logs = load_data(LOG_FILE)
    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "details": details,
        "user": user
    }
    logs.append(log_entry)
    save_data(logs, LOG_FILE)
    
def load_excel_from_firebase():
    bucket = storage.bucket()
    blob = bucket.blob('Financeiro/Posicao_clientes.xlsx')
    
    # Download do arquivo para a memória
    excel_content = blob.download_as_bytes()
    
    # Leitura do Excel usando pandas
    df = pd.read_excel(io.BytesIO(excel_content))
    return df

def main():
    st.title("Cobrança")

    # Sidebar para o log
    if st.sidebar.button("Visualizar Log"):
        logs = load_data(LOG_FILE)
        if logs:
            st.sidebar.dataframe(pd.DataFrame(logs))
        else:
            st.sidebar.info("Nenhuma ação registrada no log.")

    # Criação das abas
    tab1, tab2 = st.tabs(["Operação de Cobrança", "Cadastro de Clientes"])

    with tab1:
        st.header("Operação de Cobrança")
        
        try:
            df = load_excel_from_firebase()
            
            # Converter a coluna 'DATA' para datetime
            df['DATA'] = pd.to_datetime(df['DATA'], format='%d/%m/%Y', errors='coerce')
            
            # Filtrar os dados a partir de 09/07/2024
            data_corte = pd.to_datetime('09/07/2024')
            df_filtrado = df[df['DATA'] >= data_corte]
            
            # Exibir os dados filtrados
            st.dataframe(df_filtrado)
            
            # Adicionar mais funcionalidades de análise ou operações aqui
            
        except Exception as e:
            st.error(f"Erro ao carregar ou processar os dados: {str(e)}")

    with tab2:
        st.header("Cadastro de Clientes para Cobrança")
        
        # Formulário de cadastro
        with st.form("cadastro_cliente"):
            codigo = st.text_input("Código do Cliente")
            nome = st.text_input("Nome do Cliente")
            responsavel = st.selectbox("Responsável", ["Gerente de Vendas", "Vendedor", "Presidente"])
            registrado_por = st.session_state.user['nome_completo'] if 'user' in st.session_state else ""

            submitted = st.form_submit_button("Cadastrar Cliente")

            if submitted:
                clientes = load_data(CLIENTES_FILE)
                novo_cliente = {
                    "codigo": codigo,
                    "nome": nome,
                    "responsavel": responsavel,
                    "registrado_por": registrado_por,
                    "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                clientes.append(novo_cliente)
                save_data(clientes, CLIENTES_FILE)
                add_log("Cadastro", f"Cliente {codigo} - {nome} cadastrado", registrado_por)
                st.success("Cliente cadastrado com sucesso!")

        # Visualização e edição dos clientes cadastrados
        st.subheader("Clientes Cadastrados para Cobrança")

        clientes = load_data(CLIENTES_FILE)
        if clientes:
            df = pd.DataFrame(clientes)
            st.dataframe(df)

            # Edição e remoção de clientes
            cliente_para_acao = st.selectbox("Selecione um cliente para editar ou remover:", 
                                             options=[f"{c['codigo']} - {c['nome']}" for c in clientes])
            
            acao = st.radio("Escolha uma ação:", ["Editar", "Remover"])

            if acao == "Editar":
                cliente_selecionado = next(c for c in clientes if f"{c['codigo']} - {c['nome']}" == cliente_para_acao)
                with st.form("editar_cliente"):
                    novo_nome = st.text_input("Nome do Cliente", value=cliente_selecionado['nome'])
                    novo_responsavel = st.selectbox("Responsável", ["Gerente de Vendas", "Vendedor", "Presidente"], 
                                                    index=["Gerente de Vendas", "Vendedor", "Presidente"].index(cliente_selecionado['responsavel']))
                    
                    if st.form_submit_button("Atualizar Cliente"):
                        cliente_selecionado['nome'] = novo_nome
                        cliente_selecionado['responsavel'] = novo_responsavel
                        save_data(clientes, CLIENTES_FILE)
                        add_log("Edição", f"Cliente {cliente_selecionado['codigo']} atualizado", registrado_por)
                        st.success("Cliente atualizado com sucesso!")
                        st.experimental_rerun()

            elif acao == "Remover":
                if st.button("Confirmar Remoção"):
                    cliente_para_remover = next(c for c in clientes if f"{c['codigo']} - {c['nome']}" == cliente_para_acao)
                    clientes.remove(cliente_para_remover)
                    save_data(clientes, CLIENTES_FILE)
                    add_log("Remoção", f"Cliente {cliente_para_remover['codigo']} - {cliente_para_remover['nome']} removido", registrado_por)
                    st.success("Cliente removido com sucesso!")
                    st.experimental_rerun()

        else:
            st.info("Nenhum cliente cadastrado ainda.")

if __name__ == "__main__":
    main()