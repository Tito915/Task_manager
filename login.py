import streamlit as st
from user_manager import get_user_by_email, update_user_password

def login():
    st.header("Login")
    with st.form(key='login_form'):
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")
        submit_button = st.form_submit_button("Entrar")

    if submit_button:
        user = get_user_by_email(email)
        
        if user and user.get('senha', '') == senha:
            if senha == "123456":  # Sua senha padrão
                st.warning("Você está usando a senha padrão. Por favor, mude sua senha.")
                if mudar_senha(user):
                    st.success("Senha alterada com sucesso! Por favor, faça login novamente.")
                    st.rerun()
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
    senha_alterada = False
    with st.form(key='change_password_form'):
        nova_senha = st.text_input("Nova Senha", type="password")
        confirmar_senha = st.text_input("Confirmar Nova Senha", type="password")
        submit_button = st.form_submit_button("Mudar Senha")

    if submit_button:
        if nova_senha == confirmar_senha:
            if len(nova_senha) < 8:
                st.error("A nova senha deve ter pelo menos 8 caracteres.")
            elif nova_senha == "123456":
                st.error("Você não pode usar a senha padrão como sua nova senha.")
            else:
                if update_user_password(user['email'], nova_senha):
                    st.success("Senha alterada com sucesso!")
                    senha_alterada = True
                else:
                    st.error("Erro ao atualizar a senha. Tente novamente.")
        else:
            st.error("As senhas não coincidem. Tente novamente.")
    
    return senha_alterada

# Função auxiliar para log seguro (se necessário para depuração)
def log_seguro(mensagem):
    # Implemente um log seguro aqui, se necessário
    pass

if __name__ == "__main__":
    login()