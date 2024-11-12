import tempfile
import os
import json
import firebase_admin
from firebase_admin import credentials, storage
import streamlit as st

def load_users_from_firebase():
    try:
        blob = bucket.blob('SallesApp/users.json')
        _, temp_local_filename = tempfile.mkstemp()
        blob.download_to_filename(temp_local_filename)
        with open(temp_local_filename, 'r') as file:
            users = json.load(file)
        os.remove(temp_local_filename)
        return {user['id']: user for user in users}
    except Exception as e:
        print(f"Erro ao carregar usuários do Firebase Storage: {e}")
        return {}

def initialize_firebase():
    if not firebase_admin._apps:
        try:
            cred_path = os.path.join(os.path.dirname(__file__), 'firebase_credentials.json')
            
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
            else:
                cred_dict = st.secrets.get("FIREBASE_CREDENTIALS", None)
                if cred_dict:
                    temp_cred_path = os.path.join(os.path.dirname(__file__), 'temp_credentials.json')
                    with open(temp_cred_path, 'w') as f:
                        json.dump(cred_dict, f)
                    cred = credentials.Certificate(temp_cred_path)
                    os.remove(temp_cred_path)
                else:
                    raise ValueError("Credenciais do Firebase não encontradas")

            firebase_admin.initialize_app(cred, {
                'storageBucket': 'gerenciador-de-tarefas-mbv.appspot.com'
            })
            print("Firebase inicializado com sucesso")
        except Exception as e:
            print(f"Erro ao inicializar Firebase: {str(e)}")
            raise
    
    return storage.bucket()

try:
    bucket = initialize_firebase()
except Exception as e:
    print(f"Falha ao inicializar Firebase: {str(e)}")
    bucket = None

def save_users_to_firebase(users):
    try:
        blob = bucket.blob('SallesApp/users.json')
        users_list = list(users.values())
        users_json = json.dumps(users_list, indent=2)
        blob.upload_from_string(users_json, content_type='application/json')
        print("Usuários salvos com sucesso no Firebase Storage.")
    except Exception as e:
        print(f"Erro ao salvar usuários no Firebase Storage: {e}")

def get_user_by_email(email):
    users = load_users_from_firebase()
    return next((user for user in users.values() if user.get('email') == email), None)

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

def upload_profile_picture(user_id, image_file):
    try:
        blob = bucket.blob(f"profile_pictures/{user_id}.jpg")
        blob.upload_from_file(image_file)
        blob.make_public()
        return blob.public_url
    except Exception as e:
        print(f"Erro ao fazer upload da imagem de perfil: {e}")
        return None

def update_user_profile_picture(user_id, picture_url):
    users = load_users_from_firebase()
    if user_id in users:
        users[user_id]['profile_picture'] = picture_url
        save_users_to_firebase(users)
        return True
    return False

def get_user_profile_picture(user_id):
    users = load_users_from_firebase()
    user = users.get(user_id)
    return user.get('profile_picture') if user else None

def reload_firebase_data():
    global bucket
    bucket = initialize_firebase()

if __name__ == "__main__":
    email = "titodossantos@icloud.com"
    senha = "123456"
    user = get_user_by_email(email)
    if user and user['senha'] == senha:
        print(f"Login bem-sucedido para {user['nome_completo']}")
    else:
        print("Email ou senha incorretos.")