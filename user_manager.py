import streamlit as st
from firebase_utils import db_ref, bucket, initialize_firebase, validar_conexao
import json

# Inicializar o Firebase
try:
    initialize_firebase()
    if not validar_conexao():
        st.error("Falha na conexão com o Firebase.")
except Exception as e:
    st.error(f"Erro ao inicializar Firebase: {str(e)}")

def load_users_from_firebase():
    """Carrega usuários do Firebase."""
    try:
        users_ref = db_ref.child('SallesApp/users')
        users = users_ref.get()
        return users if users else {}
    except Exception as e:
        st.error(f"Erro ao carregar usuários do Firebase: {e}")
        return {}

def save_users_to_firebase(users):
    """Salva usuários no Firebase."""
    try:
        users_ref = db_ref.child('SallesApp/users')
        users_ref.set(users)
    except Exception as e:
        st.error(f"Erro ao salvar usuários no Firebase: {e}")

def get_user_by_email(email):
    """Busca usuário por email no Firebase."""
    users = load_users_from_firebase()
    for user_id, user in users.items():
        if user.get('email') == email:
            return user
    return None

def update_user_password(email, new_password):
    """Atualiza a senha do usuário no Firebase."""
    users = load_users_from_firebase()
    for user_id, user in users.items():
        if user.get('email') == email:
            user['senha'] = new_password
            save_users_to_firebase(users)
            return True
    return False

def add_user(user):
    """Adiciona um novo usuário no Firebase."""
    users = load_users_from_firebase()
    new_user_id = str(len(users) + 1).zfill(3)
    users[new_user_id] = user
    save_users_to_firebase(users)
    return True

def user_exists(email):
    """Verifica se um usuário com o email fornecido já existe."""
    return get_user_by_email(email) is not None

def user_has_permission(email, permission):
    """Verifica se o usuário tem uma permissão específica."""
    user = get_user_by_email(email)
    if user and user.get('funcao') == 'Desenvolvedor':
        return True
    return user and permission in user.get('permissions', [])

def add_permission(email, permission):
    """Adiciona uma permissão a um usuário."""
    users = load_users_from_firebase()
    for user_id, user in users.items():
        if user.get('email') == email:
            if 'permissions' not in user:
                user['permissions'] = []
            if permission not in user['permissions']:
                user['permissions'].append(permission)
                save_users_to_firebase(users)
                return True
    return False

def get_user_permissions(email):
    """Retorna a lista de permissões de um usuário."""
    user = get_user_by_email(email)
    return user.get('permissions', []) if user else []

# Funções adicionais para lidar com imagens de perfil

def upload_profile_picture(user_id, image_file):
    """Faz upload da imagem de perfil para o Firebase Storage."""
    if not bucket:
        st.error("Firebase Storage não inicializado")
        return None
    try:
        blob = bucket.blob(f"profile_pictures/{user_id}.jpg")
        blob.upload_from_file(image_file)
        blob.make_public()
        return blob.public_url
    except Exception as e:
        st.error(f"Erro ao fazer upload da imagem de perfil: {e}")
        return None

def update_user_profile_picture(user_id, picture_url):
    """Atualiza a URL da imagem de perfil do usuário no Firebase."""
    users = load_users_from_firebase()
    if user_id in users:
        users[user_id]['profile_picture'] = picture_url
        save_users_to_firebase(users)
        return True
    return False

def get_user_profile_picture(user_id):
    """Obtém a URL da imagem de perfil do usuário."""
    user = load_users_from_firebase().get(user_id)
    return user.get('profile_picture') if user else None