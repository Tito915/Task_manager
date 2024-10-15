import firebase_admin
import re
import io
from firebase_admin import credentials, db, storage
import os
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Inicializar o Firebase
cred = credentials.Certificate(r"C:\Users\tito\OneDrive\Documentos\curso\pythoncurso\Gerenciamento_Tarefas\gerenciador-de-tarefas-mbv-firebase-adminsdk-2c48r-b6204911e1.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://gerenciador-de-tarefas-mbv-default-rtdb.firebaseio.com/',
    'storageBucket': 'gerenciador-de-tarefas-mbv.appspot.com'
})

# Obter referências para o banco de dados e storage
db_ref = db.reference()
bucket = storage.bucket()

def validar_conexao():
    try:
        # Tenta acessar o banco de dados
        db_ref.get()
        logger.info("Conexão bem-sucedida com o Firebase!")
        return True
    except Exception as e:
        logger.error(f"Erro ao conectar ao Firebase: {str(e)}")
        return False

def listar_arquivos(pasta):
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
    # Remove caracteres não permitidos
    sanitized = re.sub(r'[^\w\-_\. ]', '_', filename)
    # Substitui espaços por underscores
    sanitized = sanitized.replace(' ', '_')
    return sanitized

def salvar_arquivo(caminho_completo, conteudo):
    try:
        # Sanitiza o caminho completo
        caminho_sanitizado = '/'.join(sanitize_filename(parte) for parte in caminho_completo.split('/'))
        
        # Faz o upload do arquivo
        blob = bucket.blob(caminho_sanitizado)
        blob.upload_from_string(conteudo)

        # Configura o arquivo para ser publicamente acessível (opcional)
        blob.make_public()

        logger.info(f"Arquivo salvo com sucesso em {caminho_sanitizado}")
        return blob.public_url
    except Exception as e:
        logger.error(f"Erro ao salvar arquivo: {str(e)}")
        raise  # Re-lança a exceção para ser capturada no nível superior

def baixar_arquivo(caminho_completo):
    try:
        print(f"Tentando baixar arquivo: {caminho_completo}")
        bucket = storage.bucket()
        blob = bucket.blob(caminho_completo)
        
        # Cria um buffer em memória
        buffer = io.BytesIO()
        # Faz o download do conteúdo do arquivo para o buffer
        blob.download_to_file(buffer)
        # Move o cursor do buffer para o início
        buffer.seek(0)
        
        print(f"Arquivo {caminho_completo} baixado com sucesso. Tamanho: {buffer.getbuffer().nbytes} bytes")
        return buffer
    except Exception as e:
        print(f"Erro ao baixar arquivo: {str(e)}")
        raise # Re-lança a exceção para ser capturada no nível superior

def criar_pasta(caminho_pasta):
    try:
        # No Firebase Storage, as pastas são virtuais e são criadas automaticamente
        # quando você salva um arquivo com um caminho que inclui a pasta.
        # Vamos criar um arquivo vazio para forçar a criação da pasta.
        caminho_sanitizado = '/'.join(sanitize_filename(parte) for parte in caminho_pasta.split('/'))
        blob = bucket.blob(f"{caminho_sanitizado}/.keep")
        blob.upload_from_string('')
        logger.info(f"Pasta {caminho_sanitizado} criada com sucesso")
    except Exception as e:
        logger.error(f"Erro ao criar pasta {caminho_pasta}: {str(e)}")
        raise  # Re-lança a exceção para ser capturada no nível superior

# Exemplo de uso:
if __name__ == "__main__":
    logger.info("Iniciando o script...")

    if validar_conexao():
        logger.info("Conexão validada com sucesso. Continuando com o resto do aplicativo...")

        try:
            # Criar uma pasta
            criar_pasta("Projeto1/Teste")

            # Salvar um arquivo
            conteudo = b"Conteudo do arquivo de teste"
            url = salvar_arquivo("Projeto1/Teste/arquivo_teste.txt", conteudo)
            if url:
                logger.info(f"Arquivo salvo. URL pública: {url}")

            # Listar arquivos
            listar_arquivos("Projeto1")

            # Baixar um arquivo
            conteudo_baixado = baixar_arquivo("Projeto1/Teste/arquivo_teste.txt")
            if conteudo_baixado:
                logger.info(f"Conteúdo do arquivo baixado: {conteudo_baixado.decode('utf-8')}")

        except Exception as e:
            logger.error(f"Erro durante a execução: {str(e)}")

    else:
        logger.error("Falha na validação da conexão. Verifique as credenciais e tente novamente.")

    logger.info("Script finalizado.")
    
def upload_profile_picture(user_id, image_file):
    bucket = storage.bucket()
    blob = bucket.blob(f"profile_pictures/{user_id}.jpg")
    blob.upload_from_file(image_file)
    blob.make_public()
    return blob.public_url

def update_user_profile_picture(user_id, picture_url):
    ref = db.reference(f'users/{user_id}')
    ref.update({'profile_picture': picture_url})

def get_user_profile_picture(user_id):
    ref = db.reference(f'users/{user_id}')
    user_data = ref.get()
    return user_data.get('profile_picture', None)