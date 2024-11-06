import streamlit as st
import user_manager

def manage_permissions():
    st.header("Gerenciamento de Permissões de Usuários")

    # Carregar todos os usuários
    users = user_manager.load_users()

    # Selecionar um usuário
    selected_user_email = st.selectbox("Selecione um usuário", [user['email'] for user in users])
    selected_user = next((user for user in users if user['email'] == selected_user_email), None)

    if selected_user:
        st.subheader(f"Gerenciar permissões para {selected_user['nome_completo']}")  # Alterado de 'nome' para 'nome_completo'

        # Lista de todas as permissões possíveis
        task_manager_permissions = [
            "ver_home", "criar_tarefas", "gerenciar_tarefas", "cadastrar_membro",
            "aprovar_tarefas", "executar_tarefas", "ver_downloads"
        ]

        sales_app_permissions = [
            "ver_visao_geral", "ver_metas_vendas", "ver_controle_fiscal",
            "ver_configuracoes", "usar_calculadora"
        ]

        # Mostrar checkboxes para cada permissão do Task Manager
        st.subheader("Permissões do Task Manager")
        new_task_manager_permissions = []
        for permission in task_manager_permissions:
            has_permission = permission in selected_user.get('permissions', [])
            if st.checkbox(permission, value=has_permission, key=f"tm_{permission}"):
                new_task_manager_permissions.append(permission)

        # Mostrar checkboxes para cada permissão do Sales App
        st.subheader("Permissões do Sales App")
        new_sales_app_permissions = []
        for permission in sales_app_permissions:
            has_permission = permission in selected_user.get('permissions', [])
            if st.checkbox(permission, value=has_permission, key=f"sa_{permission}"):
                new_sales_app_permissions.append(permission)

        # Botão para salvar as alterações
        if st.button("Salvar Alterações"):
            selected_user['permissions'] = new_task_manager_permissions + new_sales_app_permissions
            user_manager.update_user(selected_user)
            st.success("Permissões atualizadas com sucesso!")

    else:
        st.warning("Nenhum usuário selecionado")