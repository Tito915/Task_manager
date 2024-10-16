import streamlit as st
import sys
from pathlib import Path
import os

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

def show_main_content():
    st.sidebar.title("Menu")

    # Mostrar o nome do usuário
    if 'user' in st.session_state and st.session_state.user:
        first_name = st.session_state.user['nome'].split()[0]
        st.sidebar.success(f"Seja bem-vindo: {first_name}")
    else:
        st.sidebar.warning("Usuário não autenticado")
        return

    # Menu suspenso para seleção de ambiente
    ambiente = st.sidebar.selectbox("Selecione o Ambiente", ["Task Manager", "Sales App"])

    if ambiente == "Task Manager":
        # Submenu para Task Manager
        task_menu = st.sidebar.selectbox(
            "Navegação Task Manager",
            ["Home", "Tarefas", "Gerenciamento de Tarefas", "Cadastrar Membro", "Aprovar Tarefas", "Executar Tarefas", "Downloads"]
        )

        if task_menu == "Home":
            home_page()
        elif task_menu == "Tarefas":
            create_task()
        elif task_menu == "Gerenciamento de Tarefas":
            manage_tasks()
        elif task_menu == "Cadastrar Membro":
            if st.session_state.user['funcao'] in ['Desenvolvedor', 'Presidente']:
                cadastrar_membro(st.session_state.user)
            else:
                st.error("Você não tem permissão para cadastrar membros.")
        elif task_menu == "Aprovar Tarefas":
            aprovar_tarefas(st.session_state.user['nome'])
        elif task_menu == "Executar Tarefas":
            executar_tarefas(st.session_state.user['nome'])
        elif task_menu == "Downloads":
            todas_tarefas = load_tasks()
            exibir_downloads(todas_tarefas, st.session_state.user['nome'])

    elif ambiente == "Sales App":
        sales_menu = st.sidebar.selectbox(
            "Navegação Sales App",
            ["Visão Geral", "Metas de Vendas", "Controle Fiscal", "Configurações"]
        )

        try:
            if sales_menu == "Visão Geral":
                from sales_app.pages.visao_geral import main as visao_geral_main
                visao_geral_main()
            elif sales_menu == "Metas de Vendas":
                from sales_app.pages.metas_vendas import main as metas_vendas_main
                metas_vendas_main()
            elif sales_menu == "Controle Fiscal":
                from sales_app.pages.ctrl_fiscal import main as ctrl_fiscal_main
                ctrl_fiscal_main()
            elif sales_menu == "Configurações":
                from sales_app.pages.configuracoes import main as configuracoes_main
                configuracoes_main()
        except ImportError as e:
            st.error(f"Erro ao importar módulo do Sales App: {str(e)}")
        except Exception as e:
            st.error(f"Erro ao executar função do Sales App: {str(e)}")

def main():
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    if st.session_state.user is None:
        login()
    else:
        show_main_content()

if __name__ == "__main__":
    main()