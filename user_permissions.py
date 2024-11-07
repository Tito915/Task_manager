import streamlit as st
import firebase_admin
from firebase_admin import credentials, db, storage
import json
from debug_tools import add_developer_options, collect_debug_info

# Inicialização do Firebase
@st.cache_resource
def initialize_firebase():
    if not firebase_admin._apps:
        try:
            cred_dict = st.secrets["FIREBASE_CREDENTIALS"]
            if isinstance(cred_dict, dict):
                cred = credentials.Certificate(cred_dict)
            elif isinstance(cred_dict, str):
                cred = credentials.Certificate(json.loads(cred_dict))
            else:
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

def get_user_permissions(email):
    all_permissions = load_permissions()
    permissions = all_permissions.get(email, [])
    print(f"Permissões carregadas para {email}: {permissions}")
    return permissions

def user_has_permission(email, permission):
    user_permissions = get_user_permissions(email)
    return permission in user_permissions

def can_manage_permissions(user):
    return user['funcao'] == 'Desenvolvedor' or 'gerenciar_permissoes' in get_user_permissions(user['email'])

def load_permissions():
    try:
        bucket = storage.bucket()
        blob = bucket.blob(PERMISSIONS_FILE)
        
        if blob.exists():
            content = blob.download_as_text()
            return json.loads(content)
        else:
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
        print(f"Permissões salvas com sucesso: {json.dumps(permissions, ensure_ascii=False, indent=2)}")
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

def user_permissions():
    st.header("Gerenciamento de Permissões de Usuários")

    # Debug: Mostrar informações do usuário atual
    if 'user' in st.session_state:
        st.sidebar.write("Debug: Usuário Logado")
        st.sidebar.json(st.session_state.user)
    else:
        st.sidebar.write("Debug: Nenhum usuário logado")

    # Botão de Debug para Desenvolvedores
    if st.sidebar.button("Debug: Mostrar Estado da Sessão", key="debug_button_1"):
        st.sidebar.write("Debug: Estado da Sessão")
        st.sidebar.json(dict(st.session_state))

    try:
        users = load_users()
        all_permissions = load_permissions()

        if not users:
            st.warning("Nenhum usuário encontrado.")
            return

        # Usar st.session_state para manter o usuário selecionado
        if 'selected_user_email' not in st.session_state:
            st.session_state.selected_user_email = users[0]['email']

        selected_user_email = st.selectbox("Selecione um usuário", 
                                           [user['email'] for user in users],
                                           index=[user['email'] for user in users].index(st.session_state.selected_user_email),
                                           key='user_select')

        # Atualizar o usuário selecionado na session_state
        if selected_user_email != st.session_state.selected_user_email:
            st.session_state.selected_user_email = selected_user_email
            st.session_state.user_permissions = all_permissions.get(selected_user_email, [])

        selected_user = next((user for user in users if user['email'] == selected_user_email), None)

        if selected_user:
            st.subheader(f"Gerenciar permissões para {selected_user['nome_completo']}")

            task_manager_permissions = [
                "ver_home", "criar_tarefas", "gerenciar_tarefas", "cadastrar_membro",
                "aprovar_tarefas", "executar_tarefas", "ver_downloads"
            ]

            sales_app_permissions = [
                "ver_visao_geral", "ver_metas_vendas", "ver_controle_fiscal",
                "ver_configuracoes", "usar_calculadora"
            ]

            # Debug: Mostrar permissões atuais
            st.sidebar.write("Debug: Permissões Atuais")
            st.sidebar.json(st.session_state.user_permissions)

            with st.form("permissions_form"):
                grant_all = st.checkbox("Conceder todas as permissões", key="grant_all")
                
                st.subheader("Permissões do Task Manager")
                tm_permissions = {}
                for permission in task_manager_permissions:
                    tm_permissions[permission] = st.checkbox(permission, 
                                                             value=permission in st.session_state.user_permissions, 
                                                             key=f"tm_{permission}", 
                                                             disabled=grant_all)

                st.subheader("Permissões do Sales App")
                sa_permissions = {}
                for permission in sales_app_permissions:
                    sa_permissions[permission] = st.checkbox(permission, 
                                                             value=permission in st.session_state.user_permissions, 
                                                             key=f"sa_{permission}", 
                                                             disabled=grant_all)

                submitted = st.form_submit_button("Salvar Alterações")

            if submitted:
                new_permissions = []
                if grant_all:
                    new_permissions = task_manager_permissions + sales_app_permissions
                else:
                    new_permissions = [perm for perm, checked in {**tm_permissions, **sa_permissions}.items() if checked]
                
                update_user_permissions(selected_user_email, new_permissions)
                st.success("Permissões atualizadas com sucesso!")
                st.session_state.user_permissions = new_permissions

            # Debug: Mostrar permissões após alterações
            st.sidebar.write("Debug: Permissões Após Alterações")
            st.sidebar.json(st.session_state.user_permissions)

        else:
            st.warning("Nenhum usuário selecionado")

    except Exception as e:
        st.error(f"Ocorreu um erro ao gerenciar as permissões: {str(e)}")
        st.sidebar.error(f"Debug: Erro detalhado - {str(e)}")

if __name__ == "__main__":
    initialize_firebase()
    if 'user' in st.session_state and can_manage_permissions(st.session_state['user']):
        add_developer_options()
        user_permissions()
    else:
        st.error("Você não tem permissão para acessar esta página.")

    # Adicionar mais informações de debug
    if st.sidebar.button("Mostrar Informações de Debug Detalhadas", key="debug_button_2"):
        debug_info = collect_debug_info()
        st.sidebar.json(debug_info)