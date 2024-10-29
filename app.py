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

def init_session_state():
    if 'page' not in st.session_state:
        st.session_state.page = 'home'
    if 'ambiente' not in st.session_state:
        st.session_state.ambiente = 'Task Manager'
    if 'navigation_key' not in st.session_state:
        st.session_state.navigation_key = 'Home'

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
            ambiente = st.session_state.get('ambiente', 'Sales App')
            module.main(ambiente)
    except ImportError:
        st.error(f"Não foi possível carregar a página {page_name}")
    except Exception as e:
        st.error(f"Ocorreu um erro ao executar a página {page_name}: {e}")

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
    ambiente = st.sidebar.selectbox(
        "Selecione o Ambiente",
        ["Task Manager", "Sales App"],
        key='ambiente_select'
    )

    if ambiente == "Task Manager":
        task_manager_options = {
            "Home": home_page,
            "Criar Tarefas": create_task,
            "Gerenciamento de Tarefas": manage_tasks,
            "Cadastrar Membro": lambda: cadastrar_membro(st.session_state.user) if st.session_state.user['funcao'] in ['Desenvolvedor', 'Presidente'] else st.error("Sem permissão"),
            "Aprovar Tarefas": lambda: aprovar_tarefas(st.session_state.user['nome']),
            "Executar Tarefas": lambda: executar_tarefas(st.session_state.user['nome']),
            "Downloads": lambda: exibir_downloads(load_tasks(), st.session_state.user['nome'])
        }

        selected_option = st.sidebar.selectbox(
            "Navegação Task Manager",
            list(task_manager_options.keys()),
            key='task_manager_nav'
        )

        task_manager_options[selected_option]()

    elif ambiente == "Sales App":
        sales_app_options = {
            "Visão Geral": 'visao_geral',
            "Metas de Vendas": 'metas_vendas',
            "Controle Fiscal": 'ctrl_fiscal',
            "Configurações": 'configuracoes',
            "Calculadora": 'Calculadora'
        }

        selected_option = st.sidebar.selectbox(
            "Navegação Sales App",
            list(sales_app_options.keys()),
            key='sales_app_nav'
        )

        load_sales_app_page(sales_app_options[selected_option])

def main():
    # Inicializar estado da sessão
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    init_session_state()
    
    if st.session_state.user is None:
        login()
    else:
        show_main_content()

if __name__ == "__main__":
    main()