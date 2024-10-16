import os
import streamlit as st
from home_page import home_page
from create_task import create_task
from manage_tasks import manage_tasks
from member_registration import cadastrar_membro
from approve_tasks import aprovar_tarefas
from execute_tasks import executar_tarefas, exibir_downloads
from login import login
from utils import load_tasks

# Importações do Sales App
import sys
from pathlib import Path
sales_app_path = Path(__file__).parent / 'sales_app'
sys.path.append(str(sales_app_path))

def show_main_content():
    st.sidebar.title("Menu")

    # Mostrar o nome do usuário
    first_name = st.session_state.user['nome'].split()[0]
    st.sidebar.success(f"Seja bem-vindo: {first_name}")

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
            ["Visão Geral", "Metas de Vendas", "Controle Fiscal", "Adição e Remoção de Vendas", "Configurações"]
        )

        if sales_menu == "Visão Geral":
            from sales_app.pages import visao_geral
            visao_geral.main()  # Assumindo que existe uma função main() no arquivo visao_geral.py
        elif sales_menu == "Metas de Vendas":
            from sales_app.pages import metas_vendas
            metas_vendas.main()
        elif sales_menu == "Controle Fiscal":
            from sales_app.pages import ctrl_fiscal
            ctrl_fiscal.main()
        elif sales_menu == "Adição e Remoção de Vendas":
            from sales_app.pages import adicao_remocao_vendas
            adicao_remocao_vendas.main()
        elif sales_menu == "Configurações":
            from sales_app.pages import configuracoes
            configuracoes.main()

def main():
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    if st.session_state.user is None:
        login()
    else:
        show_main_content()

if __name__ == "__main__":
    main()