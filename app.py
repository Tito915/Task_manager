import streamlit as st
# Configuração da página deve ser a primeira chamada Streamlit
st.set_page_config(page_title="Task Manager & Sales App", layout="wide")
import sys
from pathlib import Path
import importlib
from approve_tasks import aprovar_tarefas
from debug_tools import add_developer_options, collect_debug_info
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Diretório atual:", os.getcwd())
print("Conteúdo do diretório atual:", os.listdir())
print("Python path:", sys.path)

# Tente listar o conteúdo do diretório 'financeiro', se existir
financeiro_dir = os.path.join(os.getcwd(), 'financeiro')
if os.path.exists(financeiro_dir):
    print("Conteúdo do diretório 'financeiro':", os.listdir(financeiro_dir))
else:
    print("O diretório 'financeiro' não existe no caminho esperado")

# Tente listar o conteúdo do diretório 'financeiro/pages', se existir
financeiro_pages_dir = os.path.join(financeiro_dir, 'pages')
if os.path.exists(financeiro_pages_dir):
    print("Conteúdo do diretório 'financeiro/pages':", os.listdir(financeiro_pages_dir))
else:
    print("O diretório 'financeiro/pages' não existe no caminho esperado")

# Importações locais
from utils import load_tasks, initialize_firebase, validar_conexao, get_user_permissions
from home_page import home_page
from create_task import create_task, init_session_state as create_task_init_session_state
from manage_tasks import manage_tasks
from member_registration import cadastrar_membro
from approve_tasks import aprovar_tarefas
from execute_tasks import executar_tarefas, exibir_downloads
from login import login
from user_permissions import user_permissions
import Filelock

# Importações do Sales App
from sales_app.pages.visao_geral import main as visao_geral_main
from sales_app.pages.metas_vendas import main as metas_vendas_main
from sales_app.pages.ctrl_fiscal import main as ctrl_fiscal_main
from sales_app.pages.configuracoes import main as configuracoes_main
from sales_app.pages.Calculadora import main as calculadora_main

try:
    from sales_app.pages.visao_geral import main as visao_geral_main
    print("Importação de visao_geral bem-sucedida")
except ImportError as e:
    print(f"Erro ao importar visao_geral: {e}")
    
# Configuração do caminho para o Sales App
sales_app_path = Path(__file__).parent / 'sales_app'
sys.path.append(str(sales_app_path))

# Importações do ambiente financeiro
from financeiro.pages.cobranca import main as cobranca_main
from financeiro.pages.validacao import main as validacao_main

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
        print(f"Usuário {user['email']} é Desenvolvedor, permissão concedida para {permission}")
        return True
    has_permission = permission in get_user_permissions(user['email'])
    print(f"Verificando permissão {permission} para {user['email']}: {has_permission}")
    return has_permission

def main():
    init_session_state()

    if 'user' not in st.session_state:
        login()
    else:
        user = st.session_state.user
        print(f"Usuário logado: {user['email']}")
        print(f"Permissões do usuário: {get_user_permissions(user['email'])}")

        st.sidebar.title(f"Bem-vindo, {user['nome_completo']}")

        # Menus para cada ambiente
        task_manager_menu = ["Home", "Criar Tarefa", "Gerenciar Tarefas", "Aprovar Tarefas", "Executar Tarefas", "Cadastrar Membro", "Downloads"]
        sales_app_menu = ["Visão Geral", "Metas de Vendas", "Controle Fiscal", "Configurações", "Calculadora"]
        financeiro_menu = ["Cobrança", "Validação"]
        
        # Escolha do ambiente
        app_choice = st.sidebar.radio("Escolha o aplicativo:", ["Task Manager", "Sales App", "Financeiro"])

        if st.session_state.page == 'user_permissions':
            user_permissions()
        elif app_choice == "Task Manager":
            choice = st.sidebar.selectbox("Menu do Task Manager", task_manager_menu)

            if choice == "Home" and user_has_permission(user, "ver_home"):
                home()
            elif choice == "Criar Tarefa" and user_has_permission(user, "criar_tarefas"):
                create_task()
            elif choice == "Gerenciar Tarefas" and user_has_permission(user, "gerenciar_tarefas"):
                manage_tasks()
            elif choice == "Aprovar Tarefas" and user_has_permission(user, "aprovar_tarefas"):
                aprovar_tarefas()
            elif choice == "Executar Tarefas" and user_has_permission(user, "executar_tarefas"):
                executar_tarefas(user['nome_completo'])
            elif choice == "Cadastrar Membro" and user_has_permission(user, "cadastrar_membro"):
                cadastrar_membro(user)
            elif choice == "Downloads" and user_has_permission(user, "ver_downloads"):
                exibir_downloads(load_tasks(), user['nome_completo'])
            else:
                st.warning("Você não tem permissão para acessar esta funcionalidade.")

        elif app_choice == "Sales App":
            choice = st.sidebar.selectbox("Menu do Sales App", sales_app_menu)

            if choice == "Visão Geral" and user_has_permission(user, "ver_visao_geral"):
                visao_geral_main()
            elif choice == "Metas de Vendas" and user_has_permission(user, "ver_metas_vendas"):
                metas_vendas_main()
            elif choice == "Controle Fiscal" and user_has_permission(user, "ver_controle_fiscal"):
                ctrl_fiscal_main()
            elif choice == "Configurações" and user_has_permission(user, "ver_configuracoes"):
                configuracoes_main()
            elif choice == "Calculadora" and user_has_permission(user, "usar_calculadora"):
                calculadora_main()
            else:
                st.warning("Você não tem permissão para acessar esta funcionalidade.")

        elif app_choice == "Financeiro":
            choice = st.sidebar.selectbox("Menu Financeiro", financeiro_menu)

            if choice == "Cobrança" and user_has_permission(user, "ver_cobranca"):
                cobranca_main()
            elif choice == "Validação" and user_has_permission(user, "ver_validacao"):
                validacao_main()
            else:
                st.warning("Você não tem permissão para acessar esta funcionalidade.")

        # Opção de Gerenciar Permissões (disponível em ambos os apps)
        if user['funcao'] == 'Desenvolvedor':
           if st.sidebar.button("Gerenciar Permissões"):
              st.session_state.page = 'user_permissions'
              st.experimental_rerun()

        if st.sidebar.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.experimental_rerun()

        # Adicionar botão de debug
        if st.sidebar.button("Debug: Mostrar Estado da Sessão"):
            st.sidebar.json(dict(st.session_state))

        # Adicionar botão para mostrar informações de debug detalhadas
        if st.sidebar.button("Mostrar Informações de Debug Detalhadas"):
            debug_info = collect_debug_info()
            st.sidebar.json(debug_info)

if __name__ == "__main__":
    main()