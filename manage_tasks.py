import streamlit as st
import streamlit.components.v1 as components
from utils import load_tasks, save_tasks, get_user_role, delete_task, clear_all_tasks, clear_all_members, verify_developer_password
from datetime import datetime
import pandas as pd
import json
import os

# Caminhos dos arquivos
TASKS_FILE = r"C:\Users\tito\OneDrive\Documentos\curso\pythoncurso\Gerenciamento_Tarefas\tasks.json"
DELETED_TASKS_FILE = r"C:\Users\tito\OneDrive\Documentos\curso\pythoncurso\Gerenciamento_Tarefas\deleted_tasks.json"

def get_initials(name):
    parts = name.split()
    return f"{parts[0][0]}{parts[-1][0]}"

def move_task_to_deleted(task_id):
    with open(TASKS_FILE, 'r', encoding='utf-8') as f:
        tasks = json.load(f)
    
    task_to_delete = next((task for task in tasks if task['id'] == task_id), None)
    if task_to_delete:
        tasks = [task for task in tasks if task['id'] != task_id]
        
        with open(TASKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, ensure_ascii=False, indent=4)
        
        if os.path.exists(DELETED_TASKS_FILE):
            with open(DELETED_TASKS_FILE, 'r', encoding='utf-8') as f:
                deleted_tasks = json.load(f)
                if not isinstance(deleted_tasks, list):
                    deleted_tasks = []
        else:
            deleted_tasks = []
        
        deleted_tasks.append(task_to_delete)
        
        with open(DELETED_TASKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(deleted_tasks, f, ensure_ascii=False, indent=4)
        
        return True
    return False

def render_task_status_matrix(tasks):
    st.subheader("Matriz de Status das Tarefas")

    # Coletar todos os membros envolvidos nas tarefas
    all_members = set()
    for task in tasks:
        all_members.update(task.get('Membros', []))

    # Criar cabeçalhos da tabela
    headers = ["Tarefa"] + list(all_members)

    # Criar dados da tabela
    table_data = []
    for task in tasks:
        row = [task.get('titulo', 'Sem título')]
        for member in all_members:
            status_approval = task.get('Status de Aprovação', {}).get(member, 'N/A')
            execution_status = task.get('Execução Membros', {}).get(member, 'N/A')
            
            if status_approval == 'N/A':
                status = 'N/A'
            elif execution_status == 'Aprovado' and task.get('status_execucao') == 'Concluído':
                status = 'Concluída'
            elif execution_status == 'Aprovado':
                status = 'Pendente'
            elif execution_status == 'Em Execução':
                status = 'Em Aprovação'
            elif execution_status == 'Em Atraso':
                status = 'Em Atraso'
            else:
                status = 'N/A'
            
            row.append(status)
        table_data.append(row)

    # Renderizar a tabela com Streamlit
    st.table(pd.DataFrame(table_data, columns=headers))

def manage_tasks():
    st.header("Gerenciamento de Tarefas")
    
    if 'user' not in st.session_state:
        st.error("Você precisa estar logado para acessar esta página.")
        return
    
    user = st.session_state.user
    user_role = get_user_role(user)
    can_edit = user_role in ['Desenvolvedor', 'Presidente']
    
    tasks = load_tasks()
    
    # Renderizar a matriz de status das tarefas
    if tasks:
        render_task_status_matrix(tasks)
    else:
        st.warning("Nenhuma tarefa encontrada para exibir na matriz.")

    # Abas
    tab1, tab2, tab3 = st.tabs(["Visão Geral", "Sub-tarefas de Correção", "Área do Desenvolvedor"])
    
    with tab1:
        # Filtros
        st.subheader("Filtros")
        status_filter = st.multiselect("Filtrar por Status", ["Não Iniciada", "Em Andamento", "Concluído", "Aguardando Correção"])

        # Quadro de Tarefas
        st.subheader("Controle de Tarefas")
        
        if tasks:
            # Aplicar filtros
            if status_filter:
                filtered_tasks = [task for task in tasks if task.get('status_execucao') in status_filter]
            else:
                filtered_tasks = tasks

            # Tabela Principal
            html_content = """
            <style>
                .task-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-family: Arial, sans-serif;
                    background-color: white;
                }
                .task-table th, .task-table td {
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }
                .task-table th {
                    background-color: #f2f2f2;
                    font-weight: bold;
                    text-align: center;
                }
                .status-nao-iniciada {
                    background-color: red;
                    color: white;
                    font-weight: bold;
                }
                .status-concluido {
                    background-color: green;
                    color: white;
                    font-weight: bold;
                }
                .status-aguardando-correcao {
                    background-color: orange;
                    color: white;
                    font-weight: bold;
                }
                .initials-circle {
                    background-color: #007bff;
                    color: white;
                    border-radius: 50%;
                    width: 30px;
                    height: 30px;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    margin: auto;
                }
            </style>
            <div style="background-color: white; padding: 10px;">
            <table class="task-table">
                <tr>
                    <th>Tarefas</th>
                    <th>Criador da tarefa</th>
                    <th>Status</th>
                    <th>Retornos</th>
                </tr>
            """
            
            for task in filtered_tasks:
                title = task.get('titulo', 'Sem título')
                creator = get_initials(task.get('criado_por', 'Desconhecido'))
                status = task.get('status_execucao', 'Não Iniciada')
                retornos = len([s for s in task.get('Execução Membros', {}).values() if s == "Retorno"])
                
                if status == 'Aguardando Correção':
                    status_class = 'status-aguardando-correcao'
                elif status == 'Não Iniciada':
                    status_class = 'status-nao-iniciada'
                elif status == 'Concluído':
                    status_class = 'status-concluido'
                else:
                    status_class = ''
                
                html_content += f"""
                <tr>
                    <td>{title}</td>
                    <td><div class="initials-circle">{creator}</div></td>
                    <td class="{status_class}">{status}</td>
                    <td>{retornos}</td>
                </tr>
                """
            
            html_content += """
            </table>
            </div>
            """
            
            # Renderizar o HTML usando st.components.v1.html
            components.html(html_content, height=400, scrolling=True)

            # Lista suspensa para seleção de tarefas
            task_titles = [task.get('titulo', 'Sem título') for task in filtered_tasks]
            selected_task_title = st.selectbox("Selecione uma tarefa para ver detalhes", [""] + task_titles)

            # Tabela de Detalhes
            st.subheader("Detalhes da Tarefa")
            if selected_task_title:
                task = next((task for task in filtered_tasks if task.get('titulo') == selected_task_title), None)
                if task:
                    details_df = pd.DataFrame({
                        "Membros": [', '.join(task.get('Membros', []))],
                        "Departamento": [task.get('Departamento', 'Não especificado')],
                        "Status de Aprovação": ['\n'.join([f"{m}: {s}" for m, s in task.get('Status de Aprovação', {}).items()])],
                        "Descrição": [task.get('descricao', 'Não especificada')],
                        "Status Tarefa": [task.get('status_execucao', 'Não Iniciada')],
                        "Etiqueta": [task.get('Etiqueta', 'Não especificada')],
                        "Cronograma": [f"{task.get('Data Início', 'N/A')} - {task.get('Data Fim', 'N/A')}"],
                        "Retornos": [len([s for s in task.get('Execução Membros', {}).values() if s == "Retorno"])]
                    })
                    st.table(details_df.T)

                    # Exibir comentários de execução
                    if task.get('comentarios_execucao'):
                        st.subheader("Comentários de Execução")
                        for membro, comentario in task['comentarios_execucao'].items():
                            st.text(f"{membro}: {comentario}")
                else:
                    st.write("Tarefa não encontrada.")
            else:
                st.write("Selecione uma tarefa para ver os detalhes.")
        else:
            st.write("Nenhuma tarefa encontrada.")

    with tab2:
        st.subheader("Sub-tarefas de Correção")
        sub_tasks = [task for task in tasks if task.get('tarefa_pai_id')]
        
        if sub_tasks:
            for sub_task in sub_tasks:
                st.write(f"Sub-tarefa: {sub_task.get('titulo', 'Sem título')} (ID: {sub_task.get('id', 'N/A')})")
                st.write(f"Tarefa pai ID: {sub_task.get('tarefa_pai_id', 'N/A')}")
                st.write(f"Status: {sub_task.get('status_execucao', 'Não Iniciada')}")
                st.write(f"Descrição: {sub_task.get('descricao', 'Não especificada')}")
                st.write("---")
        else:
            st.write("Nenhuma sub-tarefa de correção encontrada.")

    with tab3:
        if user_role == 'Desenvolvedor':
            st.subheader("Área do Desenvolvedor")
            
            # Exibir todas as tarefas com opção de apagar
            st.write("Todas as Tarefas:")
            for task in tasks:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"Título: {task.get('titulo', 'Sem título')} (ID: {task.get('id', 'N/A')})")
                with col2:
                    if st.button(f"Apagar Tarefa {task.get('id', 'N/A')}"):
                        if move_task_to_deleted(task['id']):
                            st.success(f"Tarefa {task.get('id', 'N/A')} movida para tarefas deletadas com sucesso!")
                            st.rerun()
                        else:
                            st.error(f"Erro ao apagar a tarefa {task.get('id', 'N/A')}.")
            
            # Opção para apagar todas as tarefas e membros
            st.write("---")
            password = st.text_input("Senha do Desenvolvedor", type="password")
            if st.button("Apagar Todas as Tarefas e Membros"):
                if verify_developer_password(password):
                    # Mover todas as tarefas para deleted_tasks.json antes de apagar
                    with open(TASKS_FILE, 'r', encoding='utf-8') as f:
                        all_tasks = json.load(f)
        
                    if os.path.exists(DELETED_TASKS_FILE):
                        with open(DELETED_TASKS_FILE, 'r', encoding='utf-8') as f:
                            deleted_tasks = json.load(f)
                            if not isinstance(deleted_tasks, list):
                                deleted_tasks = []
                    else:
                        deleted_tasks = []
        
                    deleted_tasks.extend(all_tasks)
        
                    with open(DELETED_TASKS_FILE, 'w', encoding='utf-8') as f:
                        json.dump(deleted_tasks, f, ensure_ascii=False, indent=4)
        
                    # Agora, limpar as tarefas e membros
                    clear_all_tasks()
                    clear_all_members()
                    st.success("Todas as tarefas foram movidas para tarefas deletadas e todos os membros foram apagados com sucesso!")
                    st.rerun()
                else:
                    st.error("Senha incorreta. Operação não autorizada.")
        else:
            st.error("Acesso não autorizado. Apenas desenvolvedores podem acessar esta área.")

if __name__ == "__main__":
    manage_tasks()