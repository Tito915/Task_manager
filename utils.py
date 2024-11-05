import streamlit as st
from streamlit.runtime.secrets import AttrDict
import firebase_admin
from firebase_admin import credentials, db, storage
import json
import os
from datetime import datetime, timedelta
from user_manager import load_users
import logging
from filelock import FileLock

# Definição de constantes
DATA_FILE = 'tasks.json'
DELETED_TASKS_FILE = 'deleted_tasks.json'
USERS_FILE = 'users.json'

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Criação do FileLock
lock = FileLock(f"{DATA_FILE}.lock")

@st.cache_resource
def initialize_firebase():
    if not firebase_admin._apps:
        try:
            # Tenta obter as credenciais do ambiente (útil para desenvolvimento local)
            cred_json = os.getenv('FIREBASE_CREDENTIALS')
            
            if cred_json:
                cred_dict = json.loads(cred_json)
            elif 'FIREBASE_CREDENTIALS' in st.secrets:
                # Se não encontrar no ambiente, tenta obter do Streamlit Secrets
                cred_dict = st.secrets["FIREBASE_CREDENTIALS"]
                if isinstance(cred_dict, AttrDict):
                    cred_dict = dict(cred_dict)
                elif isinstance(cred_dict, str):
                    cred_dict = json.loads(cred_dict)
            else:
                raise ValueError("Nenhuma credencial válida encontrada")

            # Verifica se o dicionário tem a estrutura correta
            if "type" not in cred_dict or cred_dict["type"] != "service_account":
                raise ValueError("Credenciais inválidas: 'type' deve ser 'service_account'")

            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://gerenciador-de-tarefas-mbv-default-rtdb.firebaseio.com/',
                'storageBucket': 'gerenciador-de-tarefas-mbv.appspot.com'
            })
            # Inicializar o bucket de armazenamento
            bucket = storage.bucket()
                        
            logger.info("Firebase e Storage bucket inicializados com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar Firebase ou Storage bucket: {str(e)}")
            raise

    return firebase_admin.get_app()

@st.cache_resource(ttl=timedelta(hours=2))
def validar_conexao():
    try:
        ref = db.reference('/')
        ref.get()
        logger.info("Conexão com Firebase validada com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao validar conexão com Firebase: {str(e)}")
        return False

def load_tasks():
    try:
        with lock:
            with open(DATA_FILE, 'r') as file:
                tasks = json.load(file)
                for task in tasks:
                    if isinstance(task.get('Status de Aprovação'), str):
                        task['Status de Aprovação'] = {membro: task['Status de Aprovação'] for membro in task.get('Membros', [])}
                    if 'status_execucao' not in task:
                        task['status_execucao'] = 'Não Iniciada'
        logger.info(f"Carregadas {len(tasks)} tarefas do arquivo.")
        return tasks
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Erro ao carregar tarefas: {str(e)}")
        return []
    
def save_tasks(tarefas):
    try:
        with lock:
            with open(DATA_FILE, 'w') as file:
                json.dump(tarefas, file, indent=4)
        logger.info(f"Salvas {len(tarefas)} tarefas no arquivo.")
    except Exception as e:
        logger.error(f"Erro ao salvar tarefas: {str(e)}")
        raise


def add_task(task):
    try:
        with lock:
            tasks = load_tasks()
            if tasks:
                max_id = max(t.get('id', 0) for t in tasks)
                task_id = max_id + 1
            else:
                task_id = 1
            
            task.update({
                "id": task_id,
                "titulo": task.get("titulo", "Sem título"),
                "descricao": task.get("descricao", "Sem descrição"),
                "status_execucao": "Não Iniciada",
                "Status de Aprovação": {membro: "Pendente" for membro in task.get("Membros", [])},
                "dependencias": task.get("dependencias", []),
                "tempo_previsto_inicio": task.get("tempo_previsto_inicio"),
                "tempo_real_inicio": None,
                "tempo_previsto_fim": task.get("tempo_previsto_fim"),
                "tempo_real_fim": None,
                "atraso": None
            })
            tasks.append(task)
            save_tasks(tasks)
        logger.info(f"Adicionada nova tarefa com ID {task_id}")
        return task_id
    except Exception as e:
        logger.error(f"Erro ao adicionar tarefa: {str(e)}")
        raise


def get_members_and_departments():
    if not os.path.exists(USERS_FILE):
        return []

    with open(USERS_FILE, 'r', encoding='utf-8') as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return []

def update_task(updated_task, task_index):
    tarefas = load_tasks()
    if 0 <= task_index < len(tarefas):
        tarefas[task_index] = updated_task
        save_tasks(tarefas)
    else:
        raise IndexError("Índice de tarefa inválido")

def get_task_by_id(task_id):
    tasks = load_tasks()
    for task in tasks:
        if task.get('id') == task_id:
            return task
    return None

def update_task_by_id(updated_task):
    try:
        with lock:
            tasks = load_tasks()
            for i, task in enumerate(tasks):
                if task.get('id') == updated_task.get('id'):
                    tasks[i] = updated_task
                    save_tasks(tasks)
                    logger.info(f"Atualizada tarefa com ID {updated_task.get('id')}")
                    return True
        logger.warning(f"Tarefa com ID {updated_task.get('id')} não encontrada para atualização")
        return False
    except Exception as e:
        logger.error(f"Erro ao atualizar tarefa: {str(e)}")
        raise

def get_user_role(user):
    if isinstance(user, dict):
        return user.get('funcao', 'Usuário')
    elif isinstance(user, str):
        users = load_users()
        for u in users:
            if u['nome'] == user:
                return u.get('funcao', 'Usuário')
    return 'Usuário'

def delete_task(index):
    tasks = load_tasks()
    if 0 <= index < len(tasks):
        task = tasks.pop(index)
        save_tasks(tasks)
        move_to_deleted_tasks(task)
        return True
    return False

def move_to_deleted_tasks(task):
    try:
        with open(DELETED_TASKS_FILE, 'r') as file:
            deleted_tasks = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        deleted_tasks = []
    
    task['deleted_at'] = datetime.now().isoformat()
    deleted_tasks.append(task)
    
    with open(DELETED_TASKS_FILE, 'w') as file:
        json.dump(deleted_tasks, file, indent=4)

def load_deleted_tasks():
    try:
        with open(DELETED_TASKS_FILE, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    
def clear_all_tasks():
    save_tasks([])

def clear_all_members():
    developer_email = "titodosantos@icloud.com"
    developer_password = "Ermec6sello*"
    
    try:
        with open('users.json', 'r') as file:
            users = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        users = []
    
    # Filtrar para manter apenas o desenvolvedor
    developer = next((user for user in users if user.get('email') == developer_email), None)
    
    if developer:
        # Garantir que a senha do desenvolvedor não seja alterada
        developer['senha'] = developer_password
        users = [developer]
    else:
        # Se o desenvolvedor não existir, crie-o
        users = [{
            'email': developer_email,
            'senha': developer_password,
            'nome': 'Desenvolvedor',
            'funcao': 'Desenvolvedor'
        }]
    
    with open('users.json', 'w') as file:
        json.dump(users, file, indent=4)
        
def verify_developer_password(password):
    return password == "Ermec6sello*"