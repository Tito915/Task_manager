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
        # Debug: mostre o email que está sendo buscado
        st.write(f"Buscando usuário com email: {email}")
        
        user = get_user_by_email(email)
        
        # Debug: mostre detalhes do usuário encontrado
        st.write("Usuário encontrado:")
        st.write(user)
        
        # Debug: compare as senhas
        st.write(f"Senha digitada: {senha}")
        st.write(f"Senha do usuário: {user.get('senha') if user else 'Usuário não encontrado'}")
        
        # Comparação mais flexível e com debug
        if user:
            st.write("Comparando senhas:")
            st.write(f"Digitada (strip): '{senha.strip()}'")
            st.write(f"Armazenada (strip): '{user.get('senha', '').strip()}'")
        
        if user and user.get('senha', '').strip() == senha.strip():
            # Resto do código permanece o mesmo
            if senha == "123456":  # Sua senha padrão
                st.warning("Você está usando a senha padrão. Por favor, mude sua senha.")
                mudar_senha(user)
            else:
                st.session_state.user = {
                    'email': user['email'],
                    'nome_completo': user.get('nome_completo', user.get('nome', 'Nome não definido')),
                    'primeiro_nome': user.get('nome_completo', user.get('nome', 'Nome não definido')).split()[0],
                    'funcao': user.get('funcao', 'Usuário')
                }
                st.success(f"Bem-vindo, {st.session_state.user['primeiro_nome']}!")
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
            if len(nova_senha) < 8:
                st.error("A nova senha deve ter pelo menos 8 caracteres.")
            elif nova_senha == "senha_padrao":
                st.error("Você não pode usar a senha padrão como sua nova senha.")
            else:
                if update_user_password(user['email'], nova_senha):
                    st.success("Senha alterada com sucesso!")
                    updated_user = get_user_by_email(user['email'])
                    st.session_state.user = {
                        'email': updated_user['email'],
                        'nome_completo': updated_user.get('nome_completo', updated_user.get('nome', 'Nome não definido')),
                        'primeiro_nome': updated_user.get('nome_completo', updated_user.get('nome', 'Nome não definido')).split()[0],
                        'funcao': updated_user.get('funcao', 'Usuário')
                    }
                    st.rerun()
                else:
                    st.error("Erro ao atualizar a senha. Tente novamente.")
        else:
            st.error("As senhas não coincidem. Tente novamente.")

# A função update_user_password pode permanecer no arquivo user_manager.py