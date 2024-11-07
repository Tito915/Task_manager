import json
from utils import storage

PERMISSIONS_FILE = 'SallesApp/permissions.json'

def load_permissions():
    try:
        bucket = storage.bucket()
        blob = bucket.blob(PERMISSIONS_FILE)
        
        if blob.exists():
            content = blob.download_as_text()
            return json.loads(content)
        else:
            return {}
    except Exception as e:
        print(f"Erro ao carregar permissões: {str(e)}")
        return {}

def save_permissions(permissions):
    try:
        bucket = storage.bucket()
        blob = bucket.blob(PERMISSIONS_FILE)
        blob.upload_from_string(json.dumps(permissions, ensure_ascii=False, indent=4), content_type='application/json')
    except Exception as e:
        print(f"Erro ao salvar permissões: {str(e)}")

def update_user_permissions(email, permissions):
    all_permissions = load_permissions()
    all_permissions[email] = permissions
    save_permissions(all_permissions)

def manage_permissions():
    st.header("Gerenciamento de Permissões de Usuários")

    # Carregar todos os usuários
    users = user_manager.load_users()

    # Carregar todas as permissões
    all_permissions = user_manager.load_permissions()

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
            user_manager.update_user_permissions(selected_user_email, new_permissions)
            st.success("Permissões atualizadas com sucesso!")

    else:
        st.warning("Nenhum usuário selecionado")