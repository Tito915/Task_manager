import os
import json
import streamlit as st
from utils import load_tasks, save_tasks, update_task_by_id, get_members_and_departments, print_tasks_file_content

def get_members_and_departments_cached():
    return get_members_and_departments()

def aprovar_tarefas(usuario_logado):
    st.header("Aprovação de Tarefas")
    
        # Debugar o conteúdo do arquivo tasks.json
    print_tasks_file_content()

    # Carregar informações completas do usuário
    membros_cadastrados = get_members_and_departments_cached()
    
    # Função para normalizar strings (remover espaços, converter para minúsculas)
    def normalize(s):
        return s.lower().replace(" ", "")

    # Busca flexível do usuário
    usuario_info = None
    for membro in membros_cadastrados:
        if (normalize(usuario_logado) in normalize(membro['nome']) or
            normalize(usuario_logado) == normalize(membro['email']) or
            normalize(usuario_logado) in f"{normalize(membro['nome'])}({normalize(membro['email'])})"):
            usuario_info = membro
            break

    if not usuario_info:
        st.error(f"Usuário não encontrado: {usuario_logado}")
        st.write("Membros cadastrados:")
        for membro in membros_cadastrados:
            st.write(f"- Nome: {membro['nome']}, Email: {membro['email']}")
        return

    tarefas = load_tasks()
    st.write(f"Número total de tarefas carregadas: {len(tarefas)}")
    tarefas_para_aprovar = [
        t for t in tarefas if 
        t['status'] == 'Em Aprovação' and 
        (usuario_info['nome'] in t.get('Membros', []) or
         usuario_info['email'] == t.get('membro_solicitante_email') or
         usuario_info['id'] == t.get('membro_solicitante_id')) and
        t.get('Status de Aprovação', {}).get(usuario_info['nome'], "") != "Aprovada"
    ]
    
    # Atualizar todas as tarefas para garantir que tenham 'Status de Aprovação'
    tarefas = [atualizar_status_aprovacao(tarefa) for tarefa in tarefas]
    save_tasks(tarefas)  # Salvar as tarefas atualizadas
    st.success("Tarefas atualizadas com sucesso!")
    print_tasks_file_content()  # Verificar se as alterações foram salvas corretamente

    if not tarefas_para_aprovar:
        st.info("Você não tem tarefas para serem aprovadas.")
        return

    for index, tarefa in enumerate(tarefas_para_aprovar):
        nome_tarefa = tarefa.get('titulo', "Tarefa sem nome")
        
        st.subheader(f"Tarefa: {nome_tarefa}")
        st.write(f"Descrição: {tarefa.get('descricao', 'Sem descrição')}")
        st.write(f"Membros: {', '.join(tarefa.get('Membros', []))}")
        st.write(f"Etiqueta: {tarefa.get('Etiqueta', 'Não especificada')}")
        
        if 'observacao_detalhada' in tarefa:
            st.write("Detalhes da Nota Fiscal:")
            st.text(tarefa['observacao_detalhada'])
        
        st.write("Status de Aprovação:")
        membros_pendentes = []
        for membro, status in tarefa.get('Status de Aprovação', {}).items():
            membro_primeiro_nome = membro.split()[0]
            if status == "Aprovada":
                st.write(f"- {membro_primeiro_nome}: ✅ {status}")
            elif status == "Rejeitada":
                st.write(f"- {membro_primeiro_nome}: ❌ {status}")
            else:
                st.write(f"- {membro_primeiro_nome}: ⏳ {status}")
                membros_pendentes.append(membro_primeiro_nome)

        if membros_pendentes:
            st.warning(f"Membros pendentes de aprovação: {', '.join(membros_pendentes)}")

        status_geral = "Em Aprovação" if any(status != "Aprovada" for status in tarefa.get('Status de Aprovação', {}).values()) else "Aprovada"
        st.write(f"Status geral da tarefa: {status_geral}")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(f"Aprovar '{nome_tarefa}'", key=f"aprovar_{index}"):
                nome_completo = usuario_info['nome']
                tarefa['Status de Aprovação'][nome_completo] = "Aprovada"
                
                if all(status == "Aprovada" for status in tarefa['Status de Aprovação'].values()):
                    tarefa['status'] = "Aprovada"
                else:
                    tarefa['status'] = "Em Aprovação"
                
                update_task_by_id(tarefa)
                st.success(f"Tarefa '{nome_tarefa}' aprovada por você!")
                st.rerun()
        
        with col2:
            if st.button(f"Rejeitar '{nome_tarefa}'", key=f"rejeitar_{index}"):
                if st.checkbox("Confirmar rejeição", key=f"confirmar_rejeicao_{index}"):
                    nome_completo = usuario_info['nome']
                    tarefa['Status de Aprovação'][nome_completo] = "Rejeitada"
                    tarefa['status'] = "Rejeitada"
                    
                    update_task_by_id(tarefa)
                    adicionar_tarefa_deletada(tarefa)
                    st.warning(f"Tarefa '{nome_tarefa}' rejeitada por você.")
                    st.rerun()
                else:
                    st.info("Marque a caixa de confirmação para rejeitar a tarefa.")

        with col3:
            if st.button("Desfazer Aprovação/Rejeição", key=f"desfazer_{index}"):
                nome_completo = usuario_info['nome']
                tarefa['Status de Aprovação'][nome_completo] = "Pendente"
                tarefa['status'] = "Em Aprovação"
                update_task_by_id(tarefa)
                st.info(f"Sua decisão para a tarefa '{nome_tarefa}' foi desfeita.")
                st.rerun()

def atualizar_status_aprovacao(tarefa):
    if 'Status de Aprovação' not in tarefa:
        tarefa['Status de Aprovação'] = {membro: "Pendente" for membro in tarefa.get('Membros', [])}
    return tarefa

def adicionar_tarefa_deletada(tarefa):
    inicializar_arquivo_tarefas_deletadas()
    tarefas_deletadas = carregar_tarefas_deletadas()
    tarefas_deletadas.append(tarefa)
    salvar_tarefas_deletadas(tarefas_deletadas)

def inicializar_arquivo_tarefas_deletadas():
    if not os.path.exists('tarefas_deletadas.json'):
        with open('tarefas_deletadas.json', 'w') as file:
            json.dump([], file)

def carregar_tarefas_deletadas():
    try:
        with open('tarefas_deletadas.json', 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def salvar_tarefas_deletadas(tarefas_deletadas):
    with open('tarefas_deletadas.json', 'w') as file:
        json.dump(tarefas_deletadas, file, indent=4)

def exibir_tarefas_deletadas():
    tarefas_deletadas = carregar_tarefas_deletadas()

    if tarefas_deletadas:
        st.subheader("Tarefas Deletadas")
        for tarefa in tarefas_deletadas:
            st.write(f"Nome: {tarefa.get('titulo', 'Sem título')}")
            st.write(f"Descrição: {tarefa.get('descricao', 'Sem descrição')}")
            st.write(f"Membros: {', '.join(tarefa.get('Membros', []))}")
            st.write("---")
    else:
        st.info("Não há tarefas deletadas.")

if __name__ == "__main__":
    # Simulando um usuário logado
    aprovar_tarefas()  # Você pode mudar isso para testar diferentes formas de identificação