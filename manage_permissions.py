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
        st.subheader(f"Gerenciar permissões para {selected_user['nome']}")

        # Lista de todas as permissões possíveis
        all_permissions = [
            "ver_home", "criar_tarefas", "gerenciar_tarefas", "cadastrar_membro",
            "aprovar_tarefas", "executar_tarefas", "ver_downloads",
            "ver_visao_geral", "ver_metas_vendas", "ver_controle_fiscal",
            "ver_configuracoes", "usar_calculadora"
        ]

        # Mostrar checkboxes para cada permissão
        new_permissions = []
        for permission in all_permissions:
            has_permission = permission in selected_user.get('permissions', [])
            if st.checkbox(permission, value=has_permission):
                new_permissions.append(permission)

        # Botão para salvar as alterações
        if st.button("Salvar Alterações"):
            selected_user['permissions'] = new_permissions
            user_manager.update_user(selected_user)
            st.success("Permissões atualizadas com sucesso!")

    else:
        st.warning("Nenhum usuário selecionado")