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
    primeiro_nome = st.text_input("Primeiro Nome")
    sobrenome = st.text_input("Sobrenome")
    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")
    funcao = st.selectbox("Função", ["Desenvolvedor", "Presidente", "Financeiro", "Vendas", "Gerente_Vendas"])

    if st.button("Cadastrar"):
        users = load_users()
        novo_usuario = {
            "id": str(len(users) + 1).zfill(3),
            "primeiro_nome": primeiro_nome,
            "sobrenome": sobrenome,
            "nome_completo": f"{primeiro_nome} {sobrenome}",
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
        with st.expander(f"{user['nome_completo']} - {user['funcao']}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                novo_primeiro_nome = st.text_input("Primeiro Nome", user['primeiro_nome'], key=f"primeiro_nome_{user['id']}")
            with col2:
                novo_sobrenome = st.text_input("Sobrenome", user['sobrenome'], key=f"sobrenome_{user['id']}")
            with col3:
                novo_email = st.text_input("Email", user['email'], key=f"email_{user['id']}")
            
            nova_funcao = st.selectbox("Função", ["Desenvolvedor", "Presidente", "Financeiro", "Vendas", "Gerente_Vendas"], 
                                       index=["Desenvolvedor", "Presidente", "Financeiro", "Vendas", "Gerente_Vendas"].index(user['funcao']),
                                       key=f"funcao_{user['id']}")
            
            nova_senha = st.text_input("Nova Senha (deixe em branco para manter a atual)", type="password", key=f"senha_{user['id']}")
            
            col4, col5 = st.columns(2)
            with col4:
                if st.button("Atualizar", key=f"atualizar_{user['id']}"):
                    user['primeiro_nome'] = novo_primeiro_nome
                    user['sobrenome'] = novo_sobrenome
                    user['nome_completo'] = f"{novo_primeiro_nome} {novo_sobrenome}"
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

# Atualização no arquivo user_manager.py
def save_users(users):
    with open('users.json', 'w') as file:
        json.dump(users, file, indent=4)

def add_user(user):
    users = load_users()
    users.append(user)
    save_users(users)