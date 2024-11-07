import streamlit as st
import sys
from pathlib import Path
import importlib
import user_manager
from approve_tasks import aprovar_tarefas
from debug_tools import add_developer_options
from utils import get_user_permissions

# Configuração da página deve ser a primeira chamada Streamlit
st.set_page_config(page_title="Task Manager & Sales App", layout="wide")

# Importações locais
from utils import load_tasks, initialize_firebase, validar_conexao, get_user_permissions
from home_page import home_page
from create_task import create_task, init_session_state as create_task_init_session_state
from manage_tasks import manage_tasks
from member_registration import cadastrar_membro
from approve_tasks import aprovar_tarefas
from execute_tasks import executar_tarefas, exibir_downloads
from login import login
from manage_permissions import manage_permissions

# Importações do Sales App
from sales_app.pages.visao_geral import main as visao_geral_main
from sales_app.pages.metas_vendas import main as metas_vendas_main
from sales_app.pages.ctrl_fiscal import main as ctrl_fiscal_main
from sales_app.pages.configuracoes import main as configuracoes_main
from sales_app.pages.Calculadora import main as calculadora_main

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
def home():
    home_page()
    
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
            # Substituir st.set_page_config se existir no módulo
            original_set_page_config = st.set_page_config
            st.set_page_config = lambda *args, **kwargs: None
            
            module.main()  # Chame a função main sem passar o argumento ambiente
            
            # Restaurar st.set_page_config
            st.set_page_config = original_set_page_config
    except ImportError:
        st.error(f"Não foi possível carregar a página {page_name}")
    except Exception as e:
        st.error(f"Ocorreu um erro ao executar a página {page_name}: {e}")

def normalize_ambiente(ambiente):
    # Remove espaços e converte para minúsculas
    return ambiente.replace(" ", "").lower()

def user_has_permission(user, permission):
    # Desenvolvedores têm acesso a tudo
    if user['funcao'] == 'Desenvolvedor':
        return True
    return user_manager.user_has_permission(user['email'], permission)

def show_main_content():
    st.sidebar.title("Menu")

    if 'user' in st.session_state and st.session_state.user:
        first_name = st.session_state.user['primeiro_nome']
        st.sidebar.success(f"Seja bem-vindo: {first_name}")

        approval_count, return_count, execution_count = count_pending_tasks(st.session_state.user['nome_completo'])

        st.sidebar.markdown("### Notificações")
        col1, col2, col3 = st.sidebar.columns(3)
        col1.metric("Aprovações", approval_count, delta_color="inverse")
        col2.metric("Retornos", return_count, delta_color="inverse")
        col3.metric("Execuções", execution_count, delta_color="inverse")
    else:
        st.sidebar.warning("Usuário não autenticado")
        return

    ambiente = st.sidebar.selectbox(
        "Selecione o Ambiente",
        ["Task Manager", "Sales App"],
        key='ambiente_select'
    )

    ambiente_normalizado = normalize_ambiente(ambiente)

    if ambiente_normalizado == "taskmanager":
        task_manager_options = {
            "Home": ("ver_home", home_page),
            "Criar Tarefas": ("criar_tarefas", create_task),
            "Gerenciamento de Tarefas": ("gerenciar_tarefas", manage_tasks),
            "Cadastrar Membro": ("cadastrar_membro", lambda: cadastrar_membro(st.session_state.user)),
            "Aprovar Tarefas": ("aprovar_tarefas", aprovar_tarefas),
            "Executar Tarefas": ("executar_tarefas", lambda: executar_tarefas(st.session_state.user['nome_completo'])),
            "Downloads": ("ver_downloads", lambda: exibir_downloads(load_tasks(), st.session_state.user['nome_completo'])),
            "Gerenciar Permissões": ("gerenciar_permissoes", manage_permissions)
        }

        # Se for Desenvolvedor, mostra todas as opções
        if st.session_state.user['funcao'] == 'Desenvolvedor':
            available_options = list(task_manager_options.keys())
        else:
            available_options = [option for option, (permission, _) in task_manager_options.items() 
                                 if user_has_permission(st.session_state.user, permission)]

        selected_option = st.sidebar.selectbox(
            "Navegação Task Manager",
            available_options,
            key='task_manager_nav'
        )

        if selected_option:
            _, function = task_manager_options[selected_option]
            function()

    elif ambiente_normalizado == "salesapp":
        sales_app_options = {
            "Visão Geral": ("ver_visao_geral", 'visao_geral'),
            "Metas de Vendas": ("ver_metas_vendas", 'metas_vendas'),
            "Controle Fiscal": ("ver_controle_fiscal", 'ctrl_fiscal'),
            "Configurações": ("ver_configuracoes", 'configuracoes'),
            "Calculadora": ("usar_calculadora", 'Calculadora')
        }

        # Se for Desenvolvedor, mostra todas as opções
        if st.session_state.user['funcao'] == 'Desenvolvedor':
            available_options = list(sales_app_options.keys())
        else:
            available_options = [option for option, (permission, _) in sales_app_options.items() 
                                 if user_has_permission(st.session_state.user, permission)]

        selected_option = st.sidebar.selectbox(
            "Navegação Sales App",
            available_options,
            key='sales_app_nav'
        )

        if selected_option:
            _, page = sales_app_options[selected_option]
            load_sales_app_page(page)

    # Botão de logout
    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_rerun()

    # Exibe informações do usuário logado
    st.sidebar.markdown("---")
    st.sidebar.write(f"Logado como: {st.session_state.user['nome_completo']}")
    st.sidebar.write(f"Função: {st.session_state.user['funcao']}")

def main():
    if 'user' not in st.session_state:
        login()
    else:
        user = st.session_state.user
        user_permissions = get_user_permissions(user['email'])

        st.sidebar.title(f"Bem-vindo, {user['nome_completo']}")

        # Separando os menus do Task Manager e do Sales App
        task_manager_menu = ["Home", "Criar Tarefa", "Gerenciar Tarefas", "Aprovar Tarefas", "Executar Tarefas", "Cadastrar Membro", "Downloads"]
        sales_app_menu = ["Visão Geral", "Metas de Vendas", "Controle Fiscal", "Configurações", "Calculadora"]
        
        # Adicionando opção para escolher entre Task Manager e Sales App
        app_choice = st.sidebar.radio("Escolha o aplicativo:", ["Task Manager", "Sales App"])

        if app_choice == "Task Manager":
            choice = st.sidebar.selectbox("Menu do Task Manager", task_manager_menu)

            if choice == "Home" and "ver_home" in user_permissions:
                home()
            elif choice == "Criar Tarefa" and "criar_tarefas" in user_permissions:
                create_task()
            elif choice == "Gerenciar Tarefas" and "gerenciar_tarefas" in user_permissions:
                manage_tasks()
            elif choice == "Aprovar Tarefas" and "aprovar_tarefas" in user_permissions:
                aprovar_tarefas()
            elif choice == "Executar Tarefas" and "executar_tarefas" in user_permissions:
                executar_tarefas()
            elif choice == "Cadastrar Membro" and "cadastrar_membro" in user_permissions:
                cadastrar_membro()
            elif choice == "Downloads" and "ver_downloads" in user_permissions:
                exibir_downloads()
            else:
                st.warning("Você não tem permissão para acessar esta funcionalidade.")

        elif app_choice == "Sales App":
            choice = st.sidebar.selectbox("Menu do Sales App", sales_app_menu)

            if choice == "Visão Geral" and "ver_visao_geral" in user_permissions:
                visao_geral_main()
            elif choice == "Metas de Vendas" and "ver_metas_vendas" in user_permissions:
                metas_vendas_main()
            elif choice == "Controle Fiscal" and "ver_controle_fiscal" in user_permissions:
                ctrl_fiscal_main()
            elif choice == "Configurações" and "ver_configuracoes" in user_permissions:
                configuracoes_main()
            elif choice == "Calculadora" and "usar_calculadora" in user_permissions:
                calculadora_main()
            else:
                st.warning("Você não tem permissão para acessar esta funcionalidade.")

        # Opção de Gerenciar Permissões (disponível em ambos os apps)
        if user['funcao'] == 'Desenvolvedor':
            if st.sidebar.button("Gerenciar Permissões"):
                manage_permissions()

        if st.sidebar.button("Logout"):
            del st.session_state['user']
            st.experimental_rerun()

if __name__ == "__main__":
    main()