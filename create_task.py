import streamlit as st
from datetime import datetime, time
from utils import add_task, get_members_and_departments, load_tasks, update_task_by_id
import json
import math

def create_task():
    tab1, tab2, tab3 = st.tabs(["Tarefas", "Confirmação Pix", "Consulta de Cadastro Clientes"])

    with tab1:
        tarefas_tab()

    with tab2:
        confirmacao_pix_tab()

    with tab3:
        consulta_cadastro_clientes_tab()

def tarefas_tab():
    st.header("Criar Tarefa")
    
    # Carregar membros e departamentos a partir do arquivo JSON
    membros_cadastrados = get_members_and_departments()
    nomes_membros = [membro['nome'].split()[0] for membro in membros_cadastrados]  # Apenas o primeiro nome
    primeiro_nome_para_completo = {membro['nome'].split()[0]: membro['nome'] for membro in membros_cadastrados}
    departamentos = {membro['nome'].split()[0]: membro['funcao'] for membro in membros_cadastrados}

    # Formulário para criar tarefas
    col1, col2 = st.columns([2, 1])
    with col1:
        titulo = st.text_input("Título da Tarefa")
    with col2:
        etiqueta = st.selectbox("Etiqueta", ["Urgente", "Normal", "Baixa Prioridade"])

    descricao = st.text_area("Descrição da Tarefa")

    # Três colunas iguais para Membros, Departamento e Número de Tarefas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        membros_selecionados = st.multiselect("Membros", nomes_membros)
    
    with col2:
        departamento = st.text_input("Departamento", 
                                     value=", ".join(set(departamentos.get(nome, "") for nome in membros_selecionados)), 
                                     disabled=True)
    
    with col3:
        num_tarefas = st.number_input("Número de Tarefas", min_value=1, max_value=10, step=1, value=1, key="num_tarefas_input")

    # Task List com novo layout
    task_list = {}
    
    for i in range(1, num_tarefas + 1):
        st.write(f"--- Tarefa {i} ---")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            descricao_tarefa = st.text_input(f"Descrição da Tarefa {i}", f"Descrição da tarefa {i}", key=f"descricao_{i}")
        
        with col2:
            membro_tarefa = st.selectbox(f"Membro", membros_selecionados, key=f"membro_{i}")

        # Inicializa o estado do expander se não existir
        if f"expander_{i}" not in st.session_state:
            st.session_state[f"expander_{i}"] = True

        # Cria um expander para os detalhes adicionais
        with st.expander(f"Detalhes da Tarefa {i}", expanded=st.session_state[f"expander_{i}"]):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if i > 1:
                    dependencias_tarefa = st.multiselect(
                        f"Dependências",
                        options=range(1, i),
                        format_func=lambda x: f"Tarefa {x}",
                        key=f"dependencias_{i}"
                    )
                else:
                    st.write("Sem dependências")
                    dependencias_tarefa = []
            
            with col2:
                hora_prevista = st.time_input(f"Horário Limite", value=time(9, 0), key=f"hora_{i}")
            
            with col3:
                exige_anexo = st.selectbox(f"Exige Anexo", ["Não", "Sim"], key=f"anexo_{i}")

            if st.button("OK", key=f"ok_{i}"):
                st.session_state[f"expander_{i}"] = False
                st.rerun()

        # Armazena os dados da tarefa
        task_list[i] = {
            "descricao": descricao_tarefa,
            "membro": primeiro_nome_para_completo.get(membro_tarefa, membro_tarefa),
            "horario": hora_prevista.strftime('%H:%M:%S'),
            "exige_anexo": exige_anexo == "Sim",
            "dependencias": dependencias_tarefa
        }

    data_inicio = st.date_input("Data Início Geral", key="data_inicio_geral")
    hora_inicio = st.time_input("Hora Início Geral", key="hora_inicio_geral")
    hora_fim = st.time_input("Hora Fim Geral", key="hora_fim_geral")
    opcao_diaria = st.checkbox("Opção Diária", key="opcao_diaria")
    data_fim = st.date_input("Data Fim Geral", key="data_fim_geral") if not opcao_diaria else None

    if st.button("Criar e Salvar Tarefa"):
        if not titulo or not membros_selecionados:
            st.error("Por favor, preencha o título da tarefa e selecione pelo menos um membro.")
        else:
            task = {
                "titulo": titulo,
                "descricao": descricao,
                "Membros": [primeiro_nome_para_completo.get(m, m) for m in membros_selecionados],
                "Departamento": departamento,
                "Etiqueta": etiqueta,
                "Task List": task_list,
                "Data Início": str(data_inicio),
                "Hora Início": hora_inicio.strftime('%H:%M:%S'),
                "Hora Fim": hora_fim.strftime('%H:%M:%S'),
                "Data Fim": str(data_fim) if data_fim else None,
                "status": "Pendente",
                "Status de Aprovação": {membro: "Pendente" for membro in [primeiro_nome_para_completo.get(m, m) for m in membros_selecionados]},
                "tempo_previsto_inicio": hora_inicio.isoformat(),
                "tempo_previsto_fim": hora_fim.isoformat(),
                "Anexos de Conclusão": [],
                "criado_por": st.session_state.get('user', {}).get('nome', "Usuário Desconhecido")
            }
            task_id = add_task(task)
            st.success(f"Tarefa '{titulo}' criada e salva com sucesso! ID: {task_id}")

    # Exibir tarefas criadas pelo usuário logado
    exibir_tarefas_criadas()

def confirmacao_pix_tab():
    st.header("Confirmação Pix")
    # Adicione aqui a lógica para a confirmação de Pix
    st.write("Funcionalidade de confirmação de Pix em desenvolvimento.")

def consulta_cadastro_clientes_tab():
    st.header("Consulta de Cadastro Clientes")
    # Adicione aqui a lógica para a consulta de cadastro de clientes
    st.write("Funcionalidade de consulta de cadastro de clientes em desenvolvimento.")

def exibir_tarefas_criadas():
    if 'user' not in st.session_state:
        st.warning("Você precisa fazer login para ver suas tarefas criadas.")
        return

    tarefas = load_tasks()
    nome_usuario = st.session_state.user.get('nome', "")
    tarefas_usuario = [t for t in tarefas if t.get('criado_por') == nome_usuario]
    
    if tarefas_usuario:
        st.subheader("Tarefas Criadas")
        
        # Paginação
        tarefas_por_pagina = 5
        total_paginas = math.ceil(len(tarefas_usuario) / tarefas_por_pagina)
        pagina_atual = st.selectbox("Página", range(1, total_paginas + 1), key="pagina_tarefas")
        
        inicio = (pagina_atual - 1) * tarefas_por_pagina
        fim = inicio + tarefas_por_pagina
        tarefas_pagina = tarefas_usuario[inicio:fim]
        
        for i, tarefa in enumerate(tarefas_pagina):
            with st.expander(f"Tarefa: {tarefa.get('titulo', 'Sem título')}"):
                exibir_detalhes_tarefa(tarefa)
    else:
        st.info("Você ainda não criou nenhuma tarefa.")

def exibir_detalhes_tarefa(tarefa):
    st.write(f"Título: {tarefa.get('titulo', 'Sem título')}")
    st.write(f"Descrição: {tarefa.get('descricao', 'Sem descrição')}")
    st.write(f"Etiqueta: {tarefa.get('Etiqueta', 'Não especificada')}")
    st.write(f"Membros: {', '.join(tarefa.get('Membros', []))}")
    st.write(f"Departamento: {tarefa.get('Departamento', 'Não especificado')}")
    
    for i, subtarefa in tarefa.get('Task List', {}).items():
        st.write(f"Subtarefa {i}:")
        st.write(f"  Descrição: {subtarefa.get('descricao', 'Não especificada')}")
        st.write(f"  Membro: {subtarefa.get('membro', 'Não especificado')}")
        st.write(f"  Horário Limite: {subtarefa.get('horario', 'Não especificado')}")
        st.write(f"  Exige Anexo: {'Sim' if subtarefa.get('exige_anexo') else 'Não'}")
        st.write(f"  Dependências: {', '.join(map(str, subtarefa.get('dependencias', [])))}")

    st.write("Status de Aprovação:")
    status_aprovacao = tarefa.get('Status de Aprovação', {})
    if isinstance(status_aprovacao, str):
        st.write(f"  Status geral: {status_aprovacao}")
    elif isinstance(status_aprovacao, dict):
        for membro, status in status_aprovacao.items():
            st.write(f"  {membro}: {status}")
    else:
        st.write("  Status de aprovação não disponível")

if __name__ == "__main__":
    if 'user' not in st.session_state:
        st.warning("Você precisa fazer login para criar tarefas.")
    else:
        create_task()