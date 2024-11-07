import streamlit as st
import firebase_admin
from firebase_admin import credentials, db, storage
import json

# Inicialização do Firebase (isso deve ser feito apenas uma vez, geralmente no início do seu aplicativo)
@st.cache_resource
def initialize_firebase():
    if not firebase_admin._apps:
        try:
            # Tenta obter as credenciais do Streamlit Secrets
            cred_dict = st.secrets["FIREBASE_CREDENTIALS"]
            if isinstance(cred_dict, dict):
                # Se já for um dicionário, use-o diretamente
                cred = credentials.Certificate(cred_dict)
            elif isinstance(cred_dict, str):
                # Se for uma string JSON, parse-a
                cred = credentials.Certificate(json.loads(cred_dict))
            else:
                # Se for um AttrDict, converta para um dicionário padrão
                cred = credentials.Certificate(dict(cred_dict))
            
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://gerenciador-de-tarefas-mbv-default-rtdb.firebaseio.com/',
                'storageBucket': 'gerenciador-de-tarefas-mbv.appspot.com'
            })
            print("Firebase inicializado com sucesso")
        except Exception as e:
            st.error(f"Erro ao inicializar Firebase: {str(e)}")
            raise

    return firebase_admin.get_app()

# Constantes
PERMISSIONS_FILE = 'SallesApp/permissions.json'
USERS_FILE = 'SallesApp/users.json'

def load_permissions():
    try:
        bucket = storage.bucket()
        blob = bucket.blob(PERMISSIONS_FILE)
        
        if blob.exists():
            content = blob.download_as_text()
            return json.loads(content)
        else:
            # Se o arquivo não existir, crie um novo com um dicionário vazio
            empty_permissions = {}
            save_permissions(empty_permissions)
            return empty_permissions
    except Exception as e:
        st.error(f"Erro ao carregar permissões: {str(e)}")
        return {}

def save_permissions(permissions):
    try:
        bucket = storage.bucket()
        blob = bucket.blob(PERMISSIONS_FILE)
        blob.upload_from_string(json.dumps(permissions, ensure_ascii=False, indent=4), content_type='application/json')
        print("Permissões salvas com sucesso.")
    except Exception as e:
        st.error(f"Erro ao salvar permissões: {str(e)}")

def update_user_permissions(email, permissions):
    all_permissions = load_permissions()
    all_permissions[email] = permissions
    save_permissions(all_permissions)
    print(f"Permissões atualizadas para o usuário {email}")

def load_users():
    try:
        bucket = storage.bucket()
        blob = bucket.blob(USERS_FILE)
        
        if blob.exists():
            content = blob.download_as_text()
            return json.loads(content)
        else:
            st.warning(f"Arquivo de usuários não encontrado: {USERS_FILE}")
            return []
    except Exception as e:
        st.error(f"Erro ao carregar usuários: {str(e)}")
        return []

def manage_permissions():
    st.header("Gerenciamento de Permissões de Usuários")

    try:
        # Carregar todos os usuários
        users = load_users()

        # Carregar todas as permissões
        all_permissions = load_permissions()

        if not users:
            st.warning("Nenhum usuário encontrado.")
            return

        # Selecionar um usuário
        selected_user_email = st.selectbox("Selecione um usuário", [user['email'] for user in users])
        selected_user = next((user for user in users if user['email'] == selected_user_email), None)

        if selected_user:
            st.subheader(f"Gerenciar permissões para {selected_user['nome_completo']}")

            # Lista de todas as permissões possíveis
            task_manager_permissions = [
                "ver_home", "criar_tarefas", "gerenciar_tarefas", "cadastrar_membro",
                "aprovar_tarefas", "executar_tarefas", "ver_downloads"
            ]

            sales_app_permissions = [
                "ver_visao_geral", "ver_metas_vendas", "ver_controle_fiscal",
                "ver_configuracoes", "usar_calculadora"
            ]

            # Obter as permissões atuais do usuário
            user_permissions = all_permissions.get(selected_user_email, [])

            # Mostrar checkboxes para cada permissão do Task Manager
            st.subheader("Permissões do Task Manager")
            new_task_manager_permissions = []
            for permission in task_manager_permissions:
                has_permission = permission in user_permissions
                if st.checkbox(permission, value=has_permission, key=f"tm_{permission}"):
                    new_task_manager_permissions.append(permission)

            # Mostrar checkboxes para cada permissão do Sales App
            st.subheader("Permissões do Sales App")
            new_sales_app_permissions = []
            for permission in sales_app_permissions:
                has_permission = permission in user_permissions
                if st.checkbox(permission, value=has_permission, key=f"sa_{permission}"):
                    new_sales_app_permissions.append(permission)

            # Botão para salvar as alterações
            if st.button("Salvar Alterações"):
                new_permissions = new_task_manager_permissions + new_sales_app_permissions
                update_user_permissions(selected_user_email, new_permissions)
                st.success("Permissões atualizadas com sucesso!")

        else:
            st.warning("Nenhum usuário selecionado")

    except Exception as e:
        st.error(f"Ocorreu um erro ao gerenciar as permissões: {str(e)}")
        print(f"Erro detalhado: {str(e)}")

if __name__ == "__main__":
    manage_permissions()