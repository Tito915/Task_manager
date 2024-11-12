# debug_tools.py

import streamlit as st
import json
from utils import load_tasks, get_members_and_departments_cached
import logging
import os


def debug_login_process():
    # Configuração de logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    # Debug de caminho e existência do arquivo
    users_file_path = 'users.json'
    logger.debug(f"Caminho do arquivo users.json: {os.path.abspath(users_file_path)}")
    logger.debug(f"Arquivo users.json existe: {os.path.exists(users_file_path)}")

    # Tentar ler o arquivo
    try:
        with open(users_file_path, 'r', encoding='utf-8') as file:
            users_data = json.load(file)
            logger.debug("Conteúdo do users.json:")
            logger.debug(json.dumps(users_data, indent=2))
    except FileNotFoundError:
        logger.error("Arquivo users.json não encontrado!")
        st.error("Arquivo de usuários não encontrado. Verifique o caminho.")
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON: {e}")
        st.error("Erro na estrutura do arquivo JSON. Verifique a formatação.")
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        st.error(f"Erro ao ler arquivo de usuários: {e}")

def login():
    # Adicionar chamada de debug antes do login
    debug_login_process()

    st.header("Login")
    with st.form(key='login_form'):
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")
        submit_button = st.form_submit_button("Entrar")
        
def collect_debug_info():
    debug_info = {
        "usuario_logado": st.session_state.get('user', 'Nenhum usuário logado'),
        "tarefas_carregadas": load_tasks(),
        "membros_cadastrados": get_members_and_departments_cached(),
        "session_state": {k: v for k, v in st.session_state.items() if k != 'user'},
    }
    return debug_info

def show_debug_info():
    debug_info = collect_debug_info()
    st.json(debug_info)
    
    # Opção para copiar as informações
    if st.button("Copiar Informações de Debug"):
        st.code(json.dumps(debug_info, indent=2))
        st.success("Informações de debug copiadas para a área de transferência!")

def add_developer_options():
    user = st.session_state.get('user')
    if isinstance(user, dict) and user.get('funcao') == 'Desenvolvedor':
        if st.sidebar.button("Debug Info"):
            show_debug_info()