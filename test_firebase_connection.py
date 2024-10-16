import firebase_admin
from firebase_admin import credentials, db
import json
import datetime

def test_firebase_connection():
    # Carrega as credenciais do novo arquivo JSON
    with open('firebase_credentials.json', 'r') as file:
        cred_dict = json.load(file)

    print("Conteúdo do arquivo de credenciais:")
    for key in cred_dict:
        if key != 'private_key':
            print(f"{key}: {cred_dict[key]}")
        else:
            print(f"{key}: [REDACTED]")

    print(f"\nHora atual do sistema: {datetime.datetime.now()}")

    # Inicializa o Firebase
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://gerenciador-de-tarefas-mbv-default-rtdb.firebaseio.com/'
    })

    # Tenta acessar o banco de dados
    try:
        ref = db.reference('/')
        print("\nConexão bem-sucedida!")
        print("Conteúdo da raiz do banco de dados:")
        print(ref.get())
    except Exception as e:
        print(f"\nErro ao conectar ao Firebase: {e}")

if __name__ == "__main__":
    test_firebase_connection()