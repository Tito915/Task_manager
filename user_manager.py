import json
import os
import streamlit as st
from firebase_admin import db

def load_users_local():
    """Carrega usuários do arquivo JSON local."""
    try:
        with open('users.json', 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_users_local(users):
    """Salva usuários no arquivo JSON local."""
    with open('users.json', 'w') as file:
        json.dump(users, file, indent=4)

def get_user_by_email(email):
    """
    Busca usuário por email.
    Prioriza busca no Firebase, com fallback para arquivo local.
    """
    try:
        # Tenta buscar no Firebase
        users_ref = db.reference('SallesApp/users')
        users = users_ref.get()

        # Debug: informações sobre a estrutura de usuários
        st.write("Estrutura de usuários no Firebase:")
        st.write(f"Tipo de users: {type(users)}")
        st.write(f"Conteúdo de users: {users}")

        # Verifica se é uma lista ou dicionário
        if isinstance(users, list):
            for user in users:
                if user.get('email') == email:
                    return user
        elif isinstance(users, dict):
            for key, user in users.items():
                if user.get('email') == email:
                    return user
        
        # Se não encontrar no Firebase, tenta no arquivo local
        local_users = load_users_local()
        for user in local_users:
            if user['email'] == email:
                return user
        
        return None

    except Exception as e:
        st.error(f"Erro ao buscar usuário no Firebase: {e}")
        
        # Fallback para busca local se Firebase falhar
        local_users = load_users_local()
        for user in local_users:
            if user['email'] == email:
                return user
        
        return None

def update_user_password(email, new_password):
    """
    Atualiza a senha do usuário.
    Atualiza tanto no Firebase quanto no arquivo local.
    """
    try:
        # Atualiza no Firebase
        users_ref = db.reference('SallesApp/users')
        users = users_ref.get()

        if isinstance(users, list):
            for i, user in enumerate(users):
                if user.get('email') == email:
                    users[i]['senha'] = new_password
                    users_ref.set(users)
                    break
        elif isinstance(users, dict):
            for key, user in users.items():
                if user.get('email') == email:
                    users_ref.child(key).update({'senha': new_password})
                    break

        # Atualiza no arquivo local
        local_users = load_users_local()
        for user in local_users:
            if user['email'] == email:
                user['senha'] = new_password
                break
        save_users_local(local_users)

        return True

    except Exception as e:
        st.error(f"Erro ao atualizar senha: {e}")
        return False

def add_user(user):
    """
    Adiciona um novo usuário no Firebase e no arquivo local.
    """
    try:
        # Adiciona no Firebase
        users_ref = db.reference('SallesApp/users')
        users = users_ref.get() or []
        
        if not user.get('permissions'):
            user['permissions'] = []
        
        if isinstance(users, list):
            users.append(user)
            users_ref.set(users)
        elif isinstance(users, dict):
            new_key = str(len(users) + 1).zfill(3)
            users_ref.child(new_key).set(user)

        # Adiciona no arquivo local
        local_users = load_users_local()
        local_users.append(user)
        save_users_local(local_users)

        return True

    except Exception as e:
        st.error(f"Erro ao adicionar usuário: {e}")
        return False

def user_exists(email):
    """Verifica se um usuário com o email fornecido já existe."""
    return get_user_by_email(email) is not None

def user_has_permission(email, permission):
    """Verifica se o usuário tem uma permissão específica."""
    user = get_user_by_email(email)
    
    # Desenvolvedor tem todas as permissões
    if user and user.get('funcao') == 'Desenvolvedor':
        return True
    
    return user and 'permissions' in user and permission in user.get('permissions', [])

def add_permission(email, permission):
    """Adiciona uma permissão a um usuário."""
    try:
        # Busca o usuário
        users_ref = db.reference('SallesApp/users')
        users = users_ref.get()

        if isinstance(users, list):
            for i, user in enumerate(users):
                if user.get('email') == email:
                    if 'permissions' not in user:
                        user['permissions'] = []
                    if permission not in user['permissions']:
                        user['permissions'].append(permission)
                        users_ref.set(users)
                        # Atualiza local também
                        local_users = load_users_local()
                        local_users[i]['permissions'] = user['permissions']
                        save_users_local(local_users)
                        return True
        elif isinstance(users, dict):
            for key, user in users.items():
                if user.get('email') == email:
                    permissions = user.get('permissions', [])
                    if permission not in permissions:
                        permissions.append(permission)
                        users_ref.child(key).update({'permissions': permissions})
                        return True

        return False

    except Exception as e:
        st.error(f"Erro ao adicionar permissão: {e}")
        return False

def get_user_permissions(email):
    """Retorna a lista de permissões de um usuário."""
    user = get_user_by_email(email)
    return user.get('permissions', []) if user else []