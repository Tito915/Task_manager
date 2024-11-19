# debug_tools.py

import streamlit as st
import json
from utils import load_tasks, get_members_and_departments_cached

def collect_debug_info():
    return {
        "usuario_logado": st.session_state.get('user', 'Nenhum usuário logado'),
        "tarefas_carregadas": load_tasks(),
        "membros_cadastrados": get_members_and_departments_cached(),
        "session_state": {k: v for k, v in st.session_state.items() if k != 'user'},
    }

def show_debug_info():
    debug_info = collect_debug_info()
    st.json(debug_info)
    
    # Opção para copiar as informações
    if st.button("Copiar Informações de Debug"):
        st.code(json.dumps(debug_info, indent=2))
        st.success("Informações de debug copiadas para a área de transferência!")

    if 'user' in st.session_state and st.session_state['user']['funcao'] == 'Desenvolvedor':
        st.sidebar.subheader("Debug Information")
        debug_info = collect_debug_info()
        st.json(debug_info)

def add_developer_options():
    user = st.session_state.get('user')
    if isinstance(user, dict) and user.get('funcao') == 'Desenvolvedor':
        if st.sidebar.button("Debug Info"):
            show_debug_info()