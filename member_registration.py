
import streamlit as st
import json
from user_manager import load_users, add_user, save_users


def cadastrar_membro(user):
    if user['funcao'] not in ['Desenvolvedor', 'Presidente']:
        st.error("Você não tem permissão para acessar esta página.")
        return

    st.header("Gerenciamento de Membros")

    tab1, tab2 = st.tabs(["Cadastrar Novo Membro", "Gerenciar Membros Existentes"])

    with tab1:
        cadastrar_novo_membro()

    with tab2:
        gerenciar_membros_existentes()

def cadastrar_novo_membro():
    st.subheader("Cadastrar Novo Membro")
    nome = st.text_input("Nome")
    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")
    funcao = st.selectbox("Função", ["Desenvolvedor", "Presidente", "Financeiro", "Vendas", "Gerente_Vendas"])

    if st.button("Cadastrar"):
        novo_usuario = {
            "id": str(len(load_users()) + 1).zfill(3),
            "nome": nome,
            "email": email,
            "senha": senha,
            "funcao": funcao
        }
        add_user(novo_usuario)
        st.success("Membro cadastrado com sucesso!")

def gerenciar_membros_existentes():
    st.subheader("Gerenciar Membros Existentes")
    users = load_users()
    
    for user in users:
        with st.expander(f"{user['nome']} - {user['funcao']}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                novo_nome = st.text_input("Nome", user['nome'], key=f"nome_{user['id']}")
            with col2:
                novo_email = st.text_input("Email", user['email'], key=f"email_{user['id']}")
            with col3:
                nova_funcao = st.selectbox("Função", ["Desenvolvedor", "Presidente", "Financeiro", "Vendas", "Gerente_Vendas"], 
                                           index=["Desenvolvedor", "Presidente", "Financeiro", "Vendas", "Gerente_Vendas"].index(user['funcao']),
                                           key=f"funcao_{user['id']}")
            
            nova_senha = st.text_input("Nova Senha (deixe em branco para manter a atual)", type="password", key=f"senha_{user['id']}")
            
            col4, col5 = st.columns(2)
            with col4:
                if st.button("Atualizar", key=f"atualizar_{user['id']}"):
                    user['nome'] = novo_nome
                    user['email'] = novo_email
                    user['funcao'] = nova_funcao
                    if nova_senha:
                        user['senha'] = nova_senha
                    save_users(users)
                    st.success("Membro atualizado com sucesso!")
                    st.rerun()
            
            with col5:
                if st.button("Excluir", key=f"excluir_{user['id']}"):
                    users.remove(user)
                    save_users(users)
                    st.success("Membro excluído com sucesso!")
                    st.rerun()

# Adicione esta função ao seu arquivo user_manager.py se ainda não existir
def save_users(users):
    with open('users.json', 'w') as file:
        json.dump(users, file, indent=4)