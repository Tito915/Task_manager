import json
import os

# Caminho para o arquivo local de usuários
USER_FILE_PATH = 'Task_manager/users.json'

def load_users_from_firebase():
    # Carregar usuários do arquivo local, mantendo o nome original da função
    try:
        with open(USER_FILE_PATH, 'r') as file:
            users = json.load(file)
        return {user['id']: user for user in users}
    except Exception as e:
        print(f"Erro ao carregar usuários do arquivo local: {e}")
        return {}

def save_users_to_firebase(users):
    # Salvar usuários no arquivo local, mantendo o nome original da função
    try:
        users_list = list(users.values())
        with open(USER_FILE_PATH, 'w') as file:
            json.dump(users_list, file, indent=2)
        print("Usuários salvos com sucesso no arquivo local.")
    except Exception as e:
        print(f"Erro ao salvar usuários no arquivo local: {e}")

def get_user_by_email(email):
    try:
        with open('users.json', 'r') as f:
            users = json.load(f)
        # Removendo o print que exibia todos os usuários carregados
        for user in users:
            if user.get('email') == email:
                return user
    except Exception as e:
        print(f"Erro ao carregar usuários: {e}")
    return None

def update_user_password(email, new_password):
    users = load_users_from_firebase()
    updated = False
    for user in users.values():
        if user.get('email') == email:
            user['senha'] = new_password
            updated = True
            break
    
    if updated:
        save_users_to_firebase(users)
        print(f"Senha atualizada para o usuário: {email}")
        return True
    else:
        print(f"Usuário não encontrado: {email}")
        return False

def add_user(user):
    users = load_users_from_firebase()
    new_user_id = str(len(users) + 1).zfill(3)
    user['id'] = new_user_id
    users[new_user_id] = user
    save_users_to_firebase(users)
    return True

def user_exists(email):
    return get_user_by_email(email) is not None

def user_has_permission(email, permission):
    user = get_user_by_email(email)
    if user and user.get('funcao') == 'Desenvolvedor':
        return True
    return user and permission in user.get('permissions', [])

def add_permission(email, permission):
    users = load_users_from_firebase()
    for user in users.values():
        if user.get('email') == email:
            if 'permissions' not in user:
                user['permissions'] = []
            if permission not in user['permissions']:
                user['permissions'].append(permission)
                save_users_to_firebase(users)
                return True
    return False

def get_user_permissions(email):
    user = get_user_by_email(email)
    return user.get('permissions', []) if user else []
