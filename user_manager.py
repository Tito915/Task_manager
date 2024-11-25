import json
import os

# Caminho para o arquivo local de usuários
USER_FILE_PATH = 'Task_manager/users.json'

def load_users_from_local():
    try:
        with open(USER_FILE_PATH, 'r') as file:
            users = json.load(file)
        return {user['id']: user for user in users}
    except Exception as e:
        print(f"Erro ao carregar usuários do arquivo local: {e}")
        return {}

def save_users_to_local(users):
    try:
        users_list = list(users.values())
        with open(USER_FILE_PATH, 'w') as file:
            json.dump(users_list, file, indent=2)
        print("Usuários salvos com sucesso no arquivo local.")
    except Exception as e:
        print(f"Erro ao salvar usuários no arquivo local: {e}")

def get_user_by_email(email):
    users = load_users_from_local()
    return next((user for user in users.values() if user.get('email') == email), None)

def update_user_password(email, new_password):
    users = load_users_from_local()
    updated = False
    for user in users.values():
        if user.get('email') == email:
            user['senha'] = new_password
            updated = True
            break
    
    if updated:
        save_users_to_local(users)
        print(f"Senha atualizada para o usuário: {email}")
        return True
    else:
        print(f"Usuário não encontrado: {email}")
        return False

def add_user(user):
    users = load_users_from_local()
    new_user_id = str(len(users) + 1).zfill(3)
    user['id'] = new_user_id
    users[new_user_id] = user
    save_users_to_local(users)
    return True

def user_exists(email):
    return get_user_by_email(email) is not None

def user_has_permission(email, permission):
    user = get_user_by_email(email)
    if user and user.get('funcao') == 'Desenvolvedor':
        return True
    return user and permission in user.get('permissions', [])

def add_permission(email, permission):
    users = load_users_from_local()
    for user in users.values():
        if user.get('email') == email:
            if 'permissions' not in user:
                user['permissions'] = []
            if permission not in user['permissions']:
                user['permissions'].append(permission)
                save_users_to_local(users)
                return True
    return False

def get_user_permissions(email):
    user = get_user_by_email(email)
    return user.get('permissions', []) if user else []

# Exemplo de uso
if __name__ == "__main__":
    email = "titodossantos@icloud.com"
    senha = "123456"
    user = get_user_by_email(email)
    if user and user['senha'] == senha:
        print(f"Login bem-sucedido para {user['nome_completo']}")
    else:
        print("Email ou senha incorretos.")
