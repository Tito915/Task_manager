# C:\Users\tito\OneDrive\Documentos\curso\pythoncurso\Gerenciamento_Tarefas\financeiro\pages\clientes_cobranca.py

import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, storage, db
import json
import os
import sys
from datetime import datetime

# Adicionar o caminho do diretório pai para importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import initialize_firebase, get_user_permissions, get_members_and_departments

class ClientesCobranca:
    def __init__(self, user):
        self.user = user
        initialize_firebase()
        self.bucket = storage.bucket()
        self.db = db

    def validar_permissao(self):
        """
        Valida se o usuário tem permissão para gerenciar clientes de cobrança
        """
        permissoes_validas = ['Gerente_vendas', 'Presidente']
        return self.user.get('funcao') in permissoes_validas

    def carregar_clientes_cobranca(self):
        """
        Carrega a lista de clientes de cobrança do Firebase Realtime Database
        """
        try:
            ref = self.db.reference('clientes_cobranca')
            clientes = ref.get()
            return pd.DataFrame.from_dict(clientes, orient='index') if clientes else pd.DataFrame()
        except Exception as e:
            st.error(f"Erro ao carregar clientes de cobrança: {e}")
            return pd.DataFrame()

    def adicionar_cliente(self, codigo, nome, responsavel):
        """
        Adiciona um novo cliente à lista de cobrança
        """
        try:
            # Verificar se o cliente já existe
            ref = self.db.reference('clientes_cobranca')
            clientes_existentes = ref.get() or {}
            
            # Verificar se o código já existe
            if str(codigo) in clientes_existentes:
                st.warning(f"Cliente com código {codigo} já existe.")
                return False

            # Adicionar novo cliente
            novo_cliente = {
                str(codigo): {
                    'codigo': codigo,
                    'nome': nome,
                    'responsavel': responsavel,
                    'data_cadastro': datetime.now().isoformat()
                }
            }
            ref.update(novo_cliente)
            st.success(f"Cliente {nome} adicionado com sucesso!")
            return True
        except Exception as e:
            st.error(f"Erro ao adicionar cliente: {e}")
            return False

    def remover_cliente(self, codigo):
        """
        Remove um cliente da lista de cobrança
        """
        try:
            ref = self.db.reference('clientes_cobranca')
            ref.child(str(codigo)).delete()
            st.success(f"Cliente com código {codigo} removido com sucesso!")
            return True
        except Exception as e:
            st.error(f"Erro ao remover cliente: {e}")
            return False

    def carregar_membros(self):
        """
        Carrega lista de membros para seleção de responsável
        """
        membros = get_members_and_departments()
        return [membro['nome_completo'] for membro in membros if membro.get('funcao') in ['Gerente_vendas', 'Presidente']]

def main():
    st.title("📋 Gerenciamento de Clientes para Cobrança")

    # Verificar se o usuário está logado
    if 'user' not in st.session_state:
        st.warning("Por favor, faça login primeiro.")
        return

    # Inicializar o gerenciador de clientes
    clientes_cobranca = ClientesCobranca(st.session_state.user)

    # Validar permissão
    if not clientes_cobranca.validar_permissao():
        st.warning("Você não tem permissão para acessar esta página.")
        return

    # Carregar clientes existentes
    df_clientes = clientes_cobranca.carregar_clientes_cobranca()

    # Seção de Adicionar Cliente
    st.header("➕ Adicionar Novo Cliente")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        novo_codigo = st.text_input("Código do Cliente")
    
    with col2:
        novo_nome = st.text_input("Nome do Cliente")
    
    with col3:
        responsaveis = clientes_cobranca.carregar_membros()
        novo_responsavel = st.selectbox("Responsável", responsaveis)

    if st.button("Adicionar Cliente"):
        # Validações
        if not novo_codigo:
            st.warning("Por favor, insira o código do cliente.")
        elif not novo_nome:
            st.warning("Por favor, insira o nome do cliente.")
        else:
            clientes_cobranca.adicionar_cliente(novo_codigo, novo_nome, novo_responsavel)

    # Seção de Clientes Cadastrados
    st.header("📋 Clientes Cadastrados")
    
    if not df_clientes.empty:
        # Renomear colunas para melhor legibilidade
        df_clientes.columns = ['Código', 'Nome', 'Responsável', 'Data Cadastro']
        
        # Exibir tabela
        st.dataframe(df_clientes)

        # Opção de remover cliente
        st.subheader("🗑️ Remover Cliente")
        codigo_remover = st.text_input("Código do Cliente para Remoção")
        
        if st.button("Remover Cliente"):
            if codigo_remover:
                clientes_cobranca.remover_cliente(codigo_remover)
            else:
                st.warning("Por favor, insira o código do cliente.")

    else:
        st.info("Nenhum cliente cadastrado ainda.")

if __name__ == "__main__":
    main()