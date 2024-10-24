import streamlit as st
import sys
from pathlib import Path
import importlib

# Configuração da página deve ser a primeira chamada Streamlit
st.set_page_config(page_title="Task Manager", layout="wide")

# Importações locais
from utils import load_tasks, initialize_firebase, validar_conexao
from home_page import home_page
from create_task import create_task
from manage_tasks import manage_tasks
from member_registration import cadastrar_membro
from approve_tasks import aprovar_tarefas
from execute_tasks import executar_tarefas, exibir_downloads
from login import login

# Configuração do caminho para o Sales App
sales_app_path = Path(__file__).parent / 'sales_app'
sys.path.append(str(sales_app_path))

# Inicializar Firebase
try:
    initialize_firebase()
    if validar_conexao():
        st.success("Conexão com Firebase estabelecida com sucesso!")
    else:
        st.error("Falha ao conectar com o Firebase.")
except Exception as e:
    st.error(f"Erro ao inicializar Firebase: {str(e)}")

def count_pending_tasks(user_name):
    tasks = load_tasks()
    approval_count = sum(1 for task in tasks if task.get('status') == 'Pendente' and user_name in task.get('Membros', []))
    return_count = sum(1 for task in tasks if task.get('status_execucao') == 'Aguardando Correção' and user_name in task.get('Membros', []))
    execution_count = sum(1 for task in tasks if task.get('status_execucao') == 'Não Iniciada' and user_name in task.get('Membros', []))
    return approval_count, return_count, execution_count

def load_sales_app_page(page_name):
    try:
        module = importlib.import_module(f'sales_app.pages.{page_name}')
        if hasattr(module, 'main'):
            module.main()
    except ImportError:
        st.error(f"Não foi possível carregar a página {page_name}")

def show_main_content():
    st.sidebar.title("Menu")

    # Mostrar o nome do usuário
    if 'user' in st.session_state and st.session_state.user:
        first_name = st.session_state.user['nome'].split()[0]
        st.sidebar.success(f"Seja bem-vindo: {first_name}")

        # Contar tarefas pendentes
        approval_count, return_count, execution_count = count_pending_tasks(st.session_state.user['nome'])

        # Exibir notificações
        st.sidebar.markdown("### Notificações")
        col1, col2, col3 = st.sidebar.columns(3)
        col1.metric("Aprovações", approval_count, delta_color="inverse")
        col2.metric("Retornos", return_count, delta_color="inverse")
        col3.metric("Execuções", execution_count, delta_color="inverse")

    else:
        st.sidebar.warning("Usuário não autenticado")
        return

    # Menu suspenso para seleção de ambiente
    ambiente = st.sidebar.selectbox("Selecione o Ambiente", ["Task Manager", "Sales App"])
    st.session_state['ambiente'] = ambiente

    if ambiente == "Task Manager":
        st.sidebar.subheader("Navegação Task Manager")
        
        if st.sidebar.button("Home"):
            home_page()
        if st.sidebar.button("Tarefas"):
            create_task()
        if st.sidebar.button("Gerenciamento de Tarefas"):
            manage_tasks()
        if st.sidebar.button("Cadastrar Membro"):
            if st.session_state.user['funcao'] in ['Desenvolvedor', 'Presidente']:
                cadastrar_membro(st.session_state.user)
            else:
                st.error("Você não tem permissão para cadastrar membros.")
        if st.sidebar.button("Aprovar Tarefas"):
            aprovar_tarefas(st.session_state.user['nome'])
        if st.sidebar.button("Executar Tarefas"):
            executar_tarefas(st.session_state.user['nome'])
        if st.sidebar.button("Downloads"):
            todas_tarefas = load_tasks()
            exibir_downloads(todas_tarefas, st.session_state.user['nome'])

    elif ambiente == "Sales App":
        st.sidebar.subheader("Navegação Sales App")
    
        if st.sidebar.button("Visão Geral"):
            load_sales_app_page('visao_geral')
        if st.sidebar.button("Metas de Vendas"):
            load_sales_app_page('metas_vendas')
        if st.sidebar.button("Controle Fiscal"):
            load_sales_app_page('ctrl_fiscal')
        if st.sidebar.button("Configurações"):
            load_sales_app_page('configuracoes')

def main():
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    if st.session_state.user is None:
        login()
    else:
        show_main_content()

if __name__ == "__main__":
    main()