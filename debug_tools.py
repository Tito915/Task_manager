# debug_tools.py

import streamlit as st
import json
from utils import load_tasks, get_members_and_departments_cached

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
    if st.session_state.get('user', {}).get('funcao') == 'Desenvolvedor':
        if st.sidebar.button("Debug Info"):
            show_debug_info()