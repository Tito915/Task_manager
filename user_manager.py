import json
import os

# Caminho para o arquivo JSON
USERS_FILE = 'users.json'

def load_users():
    try:
        with open(USERS_FILE, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        # Retorna uma lista vazia se o arquivo não existir ou estiver vazio/corrompido
        return []

def save_users(users):
    """Salva os usuários no arquivo JSON."""
    with open(USERS_FILE, 'w') as file:
        json.dump(users, file, indent=4)

def add_user(user):
    """Adiciona um novo usuário e salva no arquivo JSON."""
    if 'permissions' not in user:
        user['permissions'] = []  # Permissões padrão vazias
    users = load_users()
    users.append(user)
    save_users(users)

def get_user_by_email(email):
    users = load_users()
    for user in users:
        if user['email'] == email:
            return user
    return None

def update_user_password(email, new_password):
    """Atualiza a senha de um usuário específico."""
    users = load_users()
    for user in users:
        if user['email'] == email:
            user['senha'] = new_password
            save_users(users)
            return True
    return False

def update_user(updated_user):
    users = load_users()
    for i, user in enumerate(users):
        if user['email'] == updated_user['email']:
            users[i] = updated_user
            save_users(users)
            return True
    return False

def user_has_permission(email, permission):
    user = get_user_by_email(email)
    if user and 'funcao' in user and user['funcao'] == 'Desenvolvedor':
        return True
    return user and 'permissions' in user and permission in user['permissions']

def delete_user(email):
    """Remove um usuário do arquivo JSON."""
    users = load_users()
    users = [user for user in users if user['email'] != email]
    save_users(users)

def user_exists(email):
    """Verifica se um usuário com o email fornecido já existe."""
    return get_user_by_email(email) is not None

# Novas funções para gerenciar permissões

def add_permission(email, permission):
    """Adiciona uma permissão a um usuário específico."""
    users = load_users()
    for user in users:
        if user['email'] == email:
            if 'permissions' not in user:
                user['permissions'] = []
            if permission not in user['permissions']:
                user['permissions'].append(permission)
                save_users(users)
                return True
    return False

def remove_permission(email, permission):
    """Remove uma permissão de um usuário específico."""
    users = load_users()
    for user in users:
        if user['email'] == email:
            if 'permissions' in user and permission in user['permissions']:
                user['permissions'].remove(permission)
                save_users(users)
                return True
    return False

def get_user_permissions(email):
    """Retorna a lista de permissões de um usuário específico."""
    user = get_user_by_email(email)
    if user and 'permissions' in user:
        return user['permissions']
    return []
