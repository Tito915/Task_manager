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
import tempfile

# Definição de constantes
DATA_FILE = 'SallesApp/tasks.json'
DELETED_TASKS_FILE = 'SallesApp/deleted_tasks.json'
USERS_FILE = 'SallesApp/users.json'

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Criação do FileLock
lock = FileLock(f"{tempfile.gettempdir()}/tasks.json.lock")

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
            logger.info("Firebase inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar Firebase: {str(e)}")
            raise

    return firebase_admin.get_app()

@st.cache_data(ttl=3600)  # Cache por 1 hora
def get_members_and_departments_cached():
    return get_members_and_departments()

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
        bucket = storage.bucket()
        blob = bucket.blob(DATA_FILE)
        
        if blob.exists():
            content = blob.download_as_text()
            tasks = json.loads(content)
            logger.info(f"Tarefas carregadas com sucesso. Total de tarefas: {len(tasks)}")
            return tasks
        else:
            logger.warning(f"Arquivo {DATA_FILE} não encontrado no Firebase Storage. Criando um novo arquivo.")
            save_tasks([])
            return []
    except Exception as e:
        logger.error(f"Erro ao carregar tarefas do Firebase Storage: {str(e)}")
        return []

def save_tasks(tasks):
    try:
        bucket = storage.bucket()
        blob = bucket.blob(DATA_FILE)
        blob.upload_from_string(json.dumps(tasks, ensure_ascii=False, indent=4), content_type='application/json')
        logger.info(f"Tarefas salvas com sucesso no Firebase Storage. Total de tarefas: {len(tasks)}")
    except Exception as e:
        logger.error(f"Erro ao salvar tarefas no Firebase Storage: {str(e)}")

def print_tasks_file_content():
    try:
        tasks = load_tasks()
        logger.debug("Conteúdo do arquivo tasks.json:")
        logger.debug(json.dumps(tasks, ensure_ascii=False, indent=4))
    except Exception as e:
        logger.error(f"Erro ao ler o conteúdo das tarefas: {str(e)}")

def add_task(task):
    try:
        with lock:
            tasks = load_tasks()
            if tasks:
                max_id = max(t.get('id', 0) for t in tasks)
                task_id = max_id + 1
            else:
                task_id = 1
            
            # Garantir que o criador da tarefa tenha o status "Aprovada"
            criador = task.get("criado_por")
            status_aprovacao = {membro: "Pendente" for membro in task.get("Membros", [])}
            if criador:
                status_aprovacao[criador] = "Aprovada"
            
            task.update({
                "id": task_id,
                "titulo": task.get("titulo", "Sem título"),
                "descricao": task.get("descricao", "Sem descrição"),
                "status_execucao": "Não Iniciada",
                "Status de Aprovação": status_aprovacao,
                "dependencias": task.get("dependencias", []),
                "tempo_previsto_inicio": task.get("tempo_previsto_inicio"),
                "tempo_real_inicio": None,
                "tempo_previsto_fim": task.get("tempo_previsto_fim"),
                "tempo_real_fim": None,
                "atraso": None
            })
            tasks.append(task)
            save_tasks(tasks)

            # Verificar se a tarefa foi adicionada corretamente
            updated_tasks = load_tasks()
            added_task = next((t for t in updated_tasks if t['id'] == task_id), None)
            if added_task:
                logger.info(f"Tarefa adicionada com sucesso: {added_task}")
            else:
                logger.error("Erro: A tarefa não foi adicionada corretamente")

        logger.info(f"Adicionada nova tarefa com ID {task_id}")
        return task_id
    except Exception as e:
        logger.error(f"Erro ao adicionar tarefa: {str(e)}")
        raise
def get_members_and_departments():
    try:
        bucket = storage.bucket()
        blob = bucket.blob(USERS_FILE)
        
        if blob.exists():
            content = blob.download_as_text()
            users = json.loads(content)
            return users
        else:
            logger.warning(f"Arquivo {USERS_FILE} não encontrado no Firebase Storage.")
            return []
    except Exception as e:
        logger.error(f"Erro ao carregar usuários do Firebase Storage: {str(e)}")
        return []

def update_task(updated_task, task_index):
    try:
        with lock:
            tasks = load_tasks()
            if 0 <= task_index < len(tasks):
                tasks[task_index] = updated_task
                save_tasks(tasks)
                logger.info(f"Tarefa atualizada com sucesso. Índice: {task_index}")
            else:
                raise IndexError("Índice de tarefa inválido")
    except Exception as e:
        logger.error(f"Erro ao atualizar tarefa: {str(e)}")
        raise

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
            if u['nome_completo'] == user or u['primeiro_nome'] == user:
                return u.get('funcao', 'Usuário')
    return 'Usuário'

def delete_task(index):
    try:
        with lock:
            tasks = load_tasks()
            if 0 <= index < len(tasks):
                task = tasks.pop(index)
                save_tasks(tasks)
                move_to_deleted_tasks(task)
                logger.info(f"Tarefa deletada com sucesso. Índice: {index}")
                return True
            logger.warning(f"Índice de tarefa inválido para deleção: {index}")
            return False
    except Exception as e:
        logger.error(f"Erro ao deletar tarefa: {str(e)}")
        return False

def move_to_deleted_tasks(task):
    try:
        bucket = storage.bucket()
        blob = bucket.blob(DELETED_TASKS_FILE)
        
        if blob.exists():
            content = blob.download_as_text()
            deleted_tasks = json.loads(content)
        else:
            deleted_tasks = []
        
        task['deleted_at'] = datetime.now().isoformat()
        deleted_tasks.append(task)
        
        blob.upload_from_string(json.dumps(deleted_tasks, ensure_ascii=False, indent=4), content_type='application/json')
        logger.info(f"Tarefa movida para tarefas deletadas com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao mover tarefa para tarefas deletadas: {str(e)}")

def load_deleted_tasks():
    try:
        bucket = storage.bucket()
        blob = bucket.blob(DELETED_TASKS_FILE)
        
        if blob.exists():
            content = blob.download_as_text()
            deleted_tasks = json.loads(content)
            return deleted_tasks
        else:
            logger.warning(f"Arquivo {DELETED_TASKS_FILE} não encontrado no Firebase Storage.")
            return []
    except Exception as e:
        logger.error(f"Erro ao carregar tarefas deletadas do Firebase Storage: {str(e)}")
        return []

def clear_all_tasks():
    try:
        save_tasks([])
        logger.info("Todas as tarefas foram removidas com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao limpar todas as tarefas: {str(e)}")

def clear_all_members():
    developer_email = "titodosantos@icloud.com"
    developer_password = "Ermec6sello*"
    
    try:
        users = get_members_and_departments()
        
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
        
        bucket = storage.bucket()
        blob = bucket.blob(USERS_FILE)
        blob.upload_from_string(json.dumps(users, ensure_ascii=False, indent=4), content_type='application/json')
        logger.info("Membros limpos, mantendo apenas o desenvolvedor.")
    except Exception as e:
        logger.error(f"Erro ao limpar membros: {str(e)}")

def verify_developer_password(password):
    return password == "Ermec6sello*"

# Inicialização do Firebase
initialize_firebase()