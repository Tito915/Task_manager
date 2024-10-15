import firebase_admin
import re
import io
from firebase_admin import credentials, db, storage
import os
from datetime import datetime
import logging
import json
import streamlit as st

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Inicializar o Firebase
def initialize_firebase():
    if not firebase_admin._apps:
        try:
            # Primeiro, tenta usar o arquivo local de credenciais
            cred_path = os.path.join(os.path.dirname(__file__), "firebase_credentials.json")
            if os.path.exists(cred_path):
                logger.info("Usando credenciais do arquivo local")
                with open(cred_path, 'r') as file:
                    cred_dict = json.load(file)
                cred = credentials.Certificate(cred_dict)
            elif 'FIREBASE_CREDENTIALS' in st.secrets:
                logger.info("Usando credenciais do Streamlit Cloud")
                cred_dict = st.secrets["FIREBASE_CREDENTIALS"]
                if isinstance(cred_dict, dict):
                    logger.info("cred_dict é um dicionário")
                    cred = credentials.Certificate(cred_dict)
                elif hasattr(cred_dict, '__dict__'):
                    logger.info("cred_dict é um objeto com __dict__")
                    cred = credentials.Certificate(cred_dict.__dict__)
                else:
                    logger.info("cred_dict não é um dicionário nem um objeto com __dict__")
                    cred = credentials.Certificate(json.loads(cred_dict))
            else:
                raise ValueError("Nenhuma credencial válida encontrada")

            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://gerenciador-de-tarefas-mbv-default-rtdb.firebaseio.com/',
                'storageBucket': 'gerenciador-de-tarefas-mbv.appspot.com'
            })
            logger.info("Firebase inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar Firebase: {str(e)}")
            raise

    return firebase_admin.get_app()

# Inicializa o Firebase
try:
    app = initialize_firebase()
except Exception as e:
    logger.error(f"Falha ao inicializar Firebase: {str(e)}")
    app = None

# Obter referências para o banco de dados e storage
if app:
    db_ref = db.reference()
    bucket = storage.bucket()
else:
    db_ref = None
    bucket = None

def validar_conexao():
    if not app:
        logger.error("Firebase não foi inicializado corretamente")
        return False
    try:
        result = db_ref.get()
        logger.info(f"Conexão bem-sucedida com o Firebase! Dados obtidos: {result}")
        return True
    except Exception as e:
        logger.error(f"Erro ao conectar ao Firebase: {str(e)}")
        return False

def listar_arquivos(pasta):
    if not bucket:
        logger.error("Storage bucket não inicializado")
        return
    try:
        blobs = bucket.list_blobs(prefix=pasta)
        for blob in blobs:
            logger.info(f"Nome do arquivo: {blob.name}")
            logger.info(f"Tamanho: {blob.size} bytes")
            logger.info(f"Última modificação: {blob.updated}")
            logger.info("---")
    except Exception as e:
        logger.error(f"Erro ao listar arquivos: {str(e)}")

def sanitize_filename(filename):
    sanitized = re.sub(r'[^\w\-_\. ]', '_', filename)
    return sanitized.replace(' ', '_')

def salvar_arquivo(caminho_completo, conteudo):
    if not bucket:
        logger.error("Storage bucket não inicializado")
        return
    try:
        caminho_sanitizado = '/'.join(sanitize_filename(parte) for parte in caminho_completo.split('/'))
        blob = bucket.blob(caminho_sanitizado)
        blob.upload_from_string(conteudo)
        blob.make_public()
        logger.info(f"Arquivo salvo com sucesso em {caminho_sanitizado}")
        return blob.public_url
    except Exception as e:
        logger.error(f"Erro ao salvar arquivo {caminho_completo}: {str(e)}")
        raise

def baixar_arquivo(caminho_completo):
    if not bucket:
        logger.error("Storage bucket não inicializado")
        return
    try:
        logger.info(f"Tentando baixar arquivo: {caminho_completo}")
        blob = bucket.blob(caminho_completo)
        buffer = io.BytesIO()
        blob.download_to_file(buffer)
        buffer.seek(0)
        logger.info(f"Arquivo {caminho_completo} baixado com sucesso. Tamanho: {buffer.getbuffer().nbytes} bytes")
        return buffer
    except Exception as e:
        logger.error(f"Erro ao baixar arquivo {caminho_completo}: {str(e)}")
        raise

def criar_pasta(caminho_pasta):
    if not bucket:
        logger.error("Storage bucket não inicializado")
        return
    try:
        caminho_sanitizado = '/'.join(sanitize_filename(parte) for parte in caminho_pasta.split('/'))
        blob = bucket.blob(f"{caminho_sanitizado}/.keep")
        blob.upload_from_string('')
        logger.info(f"Pasta {caminho_sanitizado} criada com sucesso")
    except Exception as e:
        logger.error(f"Erro ao criar pasta {caminho_pasta}: {str(e)}")
        raise

def upload_profile_picture(user_id, image_file):
    if not bucket:
        logger.error("Storage bucket não inicializado")
        return
    blob = bucket.blob(f"profile_pictures/{user_id}.jpg")
    blob.upload_from_file(image_file)
    blob.make_public()
    return blob.public_url

def update_user_profile_picture(user_id, picture_url):
    if not db_ref:
        logger.error("Database reference não inicializada")
        return
    ref = db_ref.child(f'users/{user_id}')
    ref.update({'profile_picture': picture_url})

def get_user_profile_picture(user_id):
    if not db_ref:
        logger.error("Database reference não inicializada")
        return
    ref = db_ref.child(f'users/{user_id}')
    user_data = ref.get()
    return user_data.get('profile_picture', None) if user_data else None

if __name__ == "__main__":
    logger.info("Iniciando o script...")

    if validar_conexao():
        logger.info("Conexão validada com sucesso. Continuando com o resto do aplicativo...")

        try:
            criar_pasta("Projeto1/Teste")
            conteudo = b"Conteudo do arquivo de teste"
            url = salvar_arquivo("Projeto1/Teste/arquivo_teste.txt", conteudo)
            if url:
                logger.info(f"Arquivo salvo. URL pública: {url}")
            listar_arquivos("Projeto1")
            conteudo_baixado = baixar_arquivo("Projeto1/Teste/arquivo_teste.txt")
            if conteudo_baixado:
                logger.info(f"Conteúdo do arquivo baixado: {conteudo_baixado.decode('utf-8')}")
        except Exception as e:
            logger.error(f"Erro durante a execução: {str(e)}")
    else:
        logger.error("Falha na validação da conexão. Verifique as credenciais e tente novamente.")

    logger.info("Script finalizado.")