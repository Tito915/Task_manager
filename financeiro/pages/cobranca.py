import streamlit as st
import pandas as pd
import json
from datetime import datetime
import os
import firebase_admin
from firebase_admin import credentials, storage
from io import BytesIO

# Inicialização do Firebase
@st.cache_resource
def initialize_firebase():
    if not firebase_admin._apps:
        try:
            cred_dict = st.secrets["FIREBASE_CREDENTIALS"]
            if isinstance(cred_dict, dict):
                cred = credentials.Certificate(cred_dict)
            elif isinstance(cred_dict, str):
                cred = credentials.Certificate(json.loads(cred_dict))
            else:
                cred = credentials.Certificate(dict(cred_dict))
            
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://gerenciador-de-tarefas-mbv-default-rtdb.firebaseio.com/',
                'storageBucket': 'gerenciador-de-tarefas-mbv.appspot.com'
            })
            print("Firebase inicializado com sucesso")
        except Exception as e:
            st.error(f"Erro ao inicializar Firebase: {str(e)}")
            raise
    return firebase_admin.get_app()

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
    
    # Leitura do Excel usando pandas, pulando as primeiras linhas
    # e usando a linha 3 (índice 2) como cabeçalho
    df = pd.read_excel(BytesIO(excel_content), header=2, skiprows=[0, 1])
    return df

def normalize_column_names(df):
    # Normaliza os nomes das colunas: remove espaços extras e converte para minúsculas
    df.columns = df.columns.str.strip().str.lower()
    return df

def main():
    # Inicializar o Firebase
    initialize_firebase()
    
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
            
            # Normalizar nomes das colunas
            df = normalize_column_names(df)
            
            # Exibir as colunas disponíveis (para debug)
            st.write("Colunas disponíveis:", df.columns.tolist())
            
            # Verificar se as colunas necessárias existem
            required_columns = ['codigo', 'cliente', 'grupo', 'endereco', 'numero']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"Colunas não encontradas: {', '.join(missing_columns)}. Verifique o arquivo Excel.")
            else:
                # Exibir os dados
                st.dataframe(df)
                
                # Aqui você pode adicionar mais processamento ou filtragem dos dados
                # Por exemplo, se houver uma coluna de data, você pode filtrar por ela:
                # if 'data' in df.columns:
                #     df['data'] = pd.to_datetime(df['data'], errors='coerce')
                #     data_corte = pd.to_datetime('09/07/2024')
                #     df_filtrado = df[df['data'] >= data_corte]
                #     st.dataframe(df_filtrado)
        
        except Exception as e:
            st.error(f"Erro ao carregar ou processar os dados: {str(e)}")
            # Exibir informações detalhadas do erro (para debug)
            st.exception(e)

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