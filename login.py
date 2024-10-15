import streamlit as st
from user_manager import get_user_by_email, update_user_password
import json

def login():
    st.header("Login")
    with st.form(key='login_form'):
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")
        submit_button = st.form_submit_button("Entrar")

    if submit_button:
        user = get_user_by_email(email)
        if user and user['senha'] == senha:
            if senha == "senha_padrao":  # Substitua "senha_padrao" pela senha padrão real
                st.warning("Você está usando a senha padrão. Por favor, mude sua senha.")
                mudar_senha(user)
            else:
                st.session_state.user = user
                st.rerun()
        else:
            st.error("Email ou senha incorretos.")

def mudar_senha(user):
    st.subheader("Mudar Senha")
    with st.form(key='change_password_form'):
        nova_senha = st.text_input("Nova Senha", type="password")
        confirmar_senha = st.text_input("Confirmar Nova Senha", type="password")
        submit_button = st.form_submit_button("Mudar Senha")

    if submit_button:
        if nova_senha == confirmar_senha:
            if update_user_password(user['email'], nova_senha):
                st.success("Senha alterada com sucesso!")
                st.session_state.user = get_user_by_email(user['email'])  # Atualiza o usuário na sessão
                st.rerun()
            else:
                st.error("Erro ao atualizar a senha. Tente novamente.")
        else:
            st.error("As senhas não coincidem. Tente novamente.")

# Adicione esta função ao seu arquivo user_manager.py
def update_user_password(email, new_password):
    try:
        with open('users.json', 'r') as file:
            users = json.load(file)
        
        for user in users:
            if user['email'] == email:
                user['senha'] = new_password
                break
        
        with open('users.json', 'w') as file:
            json.dump(users, file, indent=4)
        
        return True
    except Exception as e:
        print(f"Erro ao atualizar senha: {e}")
        return False