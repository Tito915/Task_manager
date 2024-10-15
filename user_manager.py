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
    """Atualiza as informações de um usuário existente."""
    users = load_users()
    for i, user in enumerate(users):
        if user['email'] == updated_user['email']:
            users[i] = updated_user
            save_users(users)
            return True
    return False

def delete_user(email):
    """Remove um usuário do arquivo JSON."""
    users = load_users()
    users = [user for user in users if user['email'] != email]
    save_users(users)

def user_exists(email):
    """Verifica se um usuário com o email fornecido já existe."""
    return get_user_by_email(email) is not None