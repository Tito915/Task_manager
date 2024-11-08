import tempfile
import os
import json
import firebase_admin
from firebase_admin import credentials, storage
import streamlit as st

def initialize_firebase():
    if not firebase_admin._apps:
        try:
            # Tenta usar o arquivo local
            cred_path = os.path.join(os.path.dirname(__file__), 'firebase_credentials.json')
            
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
            else:
                # Se o arquivo não existir, tenta usar as credenciais do Streamlit secrets
                cred_dict = st.secrets.get("FIREBASE_CREDENTIALS", None)
                if cred_dict:
                    # Salva as credenciais em um arquivo temporário
                    temp_cred_path = os.path.join(os.path.dirname(__file__), 'temp_credentials.json')
                    with open(temp_cred_path, 'w') as f:
                        json.dump(cred_dict, f)
                    cred = credentials.Certificate(temp_cred_path)
                    # Remove o arquivo temporário após usar
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

# Inicialize o bucket globalmente
try:
    bucket = initialize_firebase()
except Exception as e:
    print(f"Falha ao inicializar Firebase: {str(e)}")
    bucket = None

def load_users_from_firebase():
    """Carrega usuários do Firebase Storage."""
    try:
        blob = bucket.blob('SallesApp/users.json')

        # Download do arquivo para um arquivo temporário
        _, temp_local_filename = tempfile.mkstemp()
        blob.download_to_filename(temp_local_filename)

        # Lê o conteúdo do arquivo
        with open(temp_local_filename, 'r') as file:
            users = json.load(file)

        # Converte a lista de usuários para um dicionário
        users_dict = {user['id']: user for user in users}

        return users_dict
    except Exception as e:
        st.error(f"Erro ao carregar usuários do Firebase Storage: {e}")
        return {}

def save_users_to_firebase(users):
    """Salva usuários no Firebase Storage."""
    try:
        blob = bucket.blob('SallesApp/users.json')

        # Converte o dicionário de usuários de volta para uma lista
        users_list = list(users.values())

        # Converte a lista de usuários para JSON
        users_json = json.dumps(users_list)

        # Faz o upload do JSON para o Storage
        blob.upload_from_string(users_json, content_type='application/json')

        st.success("Usuários salvos com sucesso no Firebase Storage.")
    except Exception as e:
        st.error(f"Erro ao salvar usuários no Firebase Storage: {e}")

def get_user_by_email(email):
    """Busca usuário por email no Firebase."""
    users = load_users_from_firebase()
    for user in users.values():
        if user.get('email') == email:
            return user
    return None

def update_user_password(email, new_password):
    """Atualiza a senha do usuário no Firebase."""
    users = load_users_from_firebase()
    for user in users.values():
        if user.get('email') == email:
            user['senha'] = new_password
            save_users_to_firebase(users)
            return True
    return False

def add_user(user):
    """Adiciona um novo usuário no Firebase."""
    users = load_users_from_firebase()
    new_user_id = str(len(users) + 1).zfill(3)
    user['id'] = new_user_id
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
    """Retorna a lista de permissões de um usuário."""
    user = get_user_by_email(email)
    return user.get('permissions', []) if user else []

def upload_profile_picture(user_id, image_file):
    """Faz upload da imagem de perfil para o Firebase Storage."""
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
    users = load_users_from_firebase()
    user = users.get(user_id)
    return user.get('profile_picture') if user else None

if __name__ == "__main__":
    # Teste as funções aqui
    email = "titodossantos@icloud.com"
    senha = "123456"
    user = get_user_by_email(email)
    if user and user['senha'] == senha:
        print(f"Login bem-sucedido para {user['nome_completo']}")
    else:
        print("Email ou senha incorretos.")