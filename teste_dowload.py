import firebase_admin
from firebase_admin import credentials, storage
import os

# Inicializar o Firebase (certifique-se de que o caminho para o arquivo de credenciais está correto)
cred = credentials.Certificate(r"C:\Users\tito\OneDrive\Documentos\curso\pythoncurso\Gerenciamento_Tarefas\gerenciador-de-tarefas-mbv-firebase-adminsdk-2c48r-b6204911e1.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'gerenciador-de-tarefas-mbv.appspot.com'
})

# Obter referência para o bucket
bucket = storage.bucket()

def baixar_arquivo(caminho_firebase, caminho_local):
    blob = bucket.blob(caminho_firebase)
    blob.download_to_filename(caminho_local)
    print(f"Arquivo baixado com sucesso: {caminho_local}")

# Lista de arquivos para baixar
arquivos = [
    "Projeto1/FIREBASE_6_TESTE/Tito_Nafitali_N_Dos_Santos/2024-10-11_10-00-35_GOVERNO_DO_ESTADO_DO_PARA_.pdf",
    "Projeto1/FIREBASE_6_TESTE/Junior_Alves/2024-10-11_10-01-00_Entrada_madeireira.xlsx"
]

# Criar pasta para os downloads se não existir
if not os.path.exists("downloads"):
    os.makedirs("downloads")

# Baixar cada arquivo
for arquivo in arquivos:
    nome_arquivo = os.path.basename(arquivo)
    caminho_local = os.path.join("downloads", nome_arquivo)
    try:
        baixar_arquivo(arquivo, caminho_local)
    except Exception as e:
        print(f"Erro ao baixar {arquivo}: {str(e)}")

print("Processo de download concluído. Verifique a pasta 'downloads'.")