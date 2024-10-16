import os
import streamlit as st
from home_page import home_page
from create_task import create_task
from manage_tasks import manage_tasks
from member_registration import cadastrar_membro
from approve_tasks import aprovar_tarefas
from execute_tasks import executar_tarefas, exibir_downloads
from PIL import Image
from login import login
from utils import load_tasks


# Importe as funções necessárias do Sales App
from sales_app import visao_geral, metas_vendas, ctrl_fiscal, adicao_remocao_vendas, configuracoes

def show_main_content():
    st.sidebar.title("Menu")

    # Mostrar o nome do usuário
    first_name = st.session_state.user['nome'].split()[0]
    st.sidebar.success(f"Seja bem-vindo: {first_name}")

    # Seleção de ambiente
    ambiente = st.sidebar.radio("Selecione o Ambiente", ["Task Manager", "Sales App"])

    if ambiente == "Task Manager":
        # Exibir ícones com números de pendências
        col1, col2 = st.sidebar.columns([1, 1])
        with col1:
            st.write("🔔")
            st.write("Aprovações: 2")  # Substitua por lógica real

        with col2:
            st.write("⚠️")
            st.write("Tarefas: 3")  # Substitua por lógica real

        menu = st.sidebar.radio("Navegação", ["Home", "Tarefas", "Gerenciamento de Tarefas", "Cadastrar Membro", "Aprovar Tarefas", "Executar Tarefas", "Downloads"])

        if menu == "Home":
            home_page()
        elif menu == "Tarefas":
            create_task()
        elif menu == "Gerenciamento de Tarefas":
            manage_tasks()
        elif menu == "Cadastrar Membro":
            if st.session_state.user['funcao'] in ['Desenvolvedor', 'Presidente']:
                cadastrar_membro(st.session_state.user)
            else:
                st.error("Você não tem permissão para cadastrar membros.")
        elif menu == "Aprovar Tarefas":
            aprovar_tarefas(st.session_state.user['nome'])
        elif menu == "Executar Tarefas":
            executar_tarefas(st.session_state.user['nome'])
        elif menu == "Downloads":
            todas_tarefas = load_tasks()
            exibir_downloads(todas_tarefas, st.session_state.user['nome'])

    elif ambiente == "Sales App":
        menu = st.sidebar.radio("Navegação Sales App", ["Visão Geral", "Metas de Vendas", "Controle Fiscal", "Adição e Remoção de Vendas", "Configurações"])

        if menu == "Visão Geral":
            visao_geral()
        elif menu == "Metas de Vendas":
            metas_vendas()
        elif menu == "Controle Fiscal":
            ctrl_fiscal()
        elif menu == "Adição e Remoção de Vendas":
            adicao_remocao_vendas()
        elif menu == "Configurações":
            configuracoes()

def main():
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    if st.session_state.user is None:
        login()
    else:
        show_main_content()

if __name__ == "__main__":
    main()