import json
import os
from datetime import datetime
from user_manager import load_users

# Caminho para os arquivos JSON
DATA_FILE = 'tasks.json'
DELETED_TASKS_FILE = 'deleted_tasks.json'

def load_tasks():
    try:
        with open(DATA_FILE, 'r') as file:
            tasks = json.load(file)
            for task in tasks:
                # Converter Status de Aprovação para dicionário se for string
                if isinstance(task.get('Status de Aprovação'), str):
                    task['Status de Aprovação'] = {membro: task['Status de Aprovação'] for membro in task.get('Membros', [])}
                # Garantir que status_execucao exista
                if 'status_execucao' not in task:
                    task['status_execucao'] = 'Não Iniciada'
            return tasks
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_tasks(tarefas):
    with open(DATA_FILE, 'w') as file:
        json.dump(tarefas, file, indent=4)

def add_task(task):
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
    return task_id

def get_members_and_departments(json_file='users.json'):
    if not os.path.exists(json_file):
        return []

    with open(json_file, 'r', encoding='utf-8') as file:
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
    tasks = load_tasks()
    for i, task in enumerate(tasks):
        if task.get('id') == updated_task.get('id'):
            tasks[i] = updated_task
            save_tasks(tasks)
            return True
    return False

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