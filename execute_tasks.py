import streamlit as st
import logging
import firebase_admin
import tempfile
from utils import load_tasks, save_tasks, update_task_by_id, add_task
from datetime import datetime, timedelta
import os
import time
from firebase_utils import salvar_arquivo, baixar_arquivo, criar_pasta, sanitize_filename
from firebase_admin import storage

# Configuração do logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def resetar_tarefas_diarias(tarefas):
    hoje = datetime.now().date()
    for tarefa in tarefas:
        if tarefa.get('Opção diária') and tarefa.get('status_execucao') == "Concluído":
            ultima_execucao = datetime.fromisoformat(tarefa.get('ultima_execucao', '2000-01-01')).date()
            if ultima_execucao < hoje:
                tarefa['status_execucao'] = "Não Iniciada"
                tarefa['Execução Membros'] = {membro: "Não Concluído" for membro in tarefa['Membros']}
                if 'tempo_execucao' in tarefa:
                    del tarefa['tempo_execucao']
                update_task_by_id(tarefa)

def tarefa_aprovada(tarefa):
    return tarefa.get('status') == "Aprovada"

def tarefa_disponivel_para_usuario(tarefa, usuario, todas_tarefas):
    if tarefa.get("status_execucao") == "Concluído" and not tarefa.get('Opção diária'):
        return False
    
    primeiro_nome_usuario = usuario.split()[0]
    
    if not any(primeiro_nome_usuario == membro.split()[0] for membro in tarefa.get("Membros", [])):
        return False
    
    execucao_membros = tarefa.get('Execução Membros', {})
    if not execucao_membros:
        return True
    
    nome_completo = next((membro for membro in tarefa.get("Membros", []) if membro.split()[0] == primeiro_nome_usuario), None)
    
    # Verificar dependências
    for dep_id in tarefa.get("dependencias", []):
        dep_tarefa = next((t for t in todas_tarefas if t.get("id") == dep_id), None)
        if dep_tarefa and dep_tarefa.get("status_execucao") != "Concluído":
            return False

    return nome_completo and execucao_membros.get(nome_completo) != "Concluído"

def executar_tarefas(usuario_logado):
    st.header("Execução de Tarefas")

    tarefas = load_tasks()
    
    resetar_tarefas_diarias(tarefas)

    tarefas_disponiveis = [
        (i, tarefa) for i, tarefa in enumerate(tarefas)
        if tarefa_disponivel_para_usuario(tarefa, usuario_logado, tarefas)
    ]

    tarefas_pendentes_aprovacao = [
        (i, tarefa) for i, tarefa in enumerate(tarefas)
        if not tarefa_aprovada(tarefa) and tarefa_disponivel_para_usuario(tarefa, usuario_logado, tarefas)
    ]

    if tarefas_pendentes_aprovacao:
        st.warning("Tarefas pendentes de aprovação:")
        for i, tarefa in tarefas_pendentes_aprovacao:
            titulo_tarefa = tarefa.get('titulo') or f"Tarefa {tarefa.get('id', 'sem ID')}"
            id_tarefa = tarefa.get('id', 'N/A')
            st.write(f"- {titulo_tarefa} (ID: {id_tarefa})")
        
    if not tarefas_disponiveis:
        st.info("Não há tarefas disponíveis para execução.")
        return

    for index, tarefa in tarefas_disponiveis:
        exibir_tarefa(index, tarefa, usuario_logado, tarefas)

def criar_sub_tarefa_correcao(tarefa_original, membro_solicitante, comentario):
    sub_tarefa = {
        "titulo": f"Correção: {tarefa_original['titulo']}",
        "descricao": f"Correção solicitada por {membro_solicitante}. Comentário: {comentario}",
        "status": "Aprovada",  # Aprovada automaticamente para agilizar o processo
        "status_execucao": "Não Iniciada",
        "Membros": [tarefa_original['Membros'][0]],  # Atribui ao primeiro membro da tarefa original
        "tarefa_pai_id": tarefa_original['id'],
        "prioridade": "Alta",
        "data_criacao": datetime.now().isoformat(),
        "Opção diária": False
    }
    novo_id = add_task(sub_tarefa)
    return novo_id
        
def baixar_arquivo(caminho_arquivo):
    try:
        bucket = storage.bucket()
        blob = bucket.blob(caminho_arquivo)
        return blob.download_as_bytes()
    except Exception as e:
        logger.error(f"Erro ao baixar arquivo: {str(e)}")
        return None
    
def exibir_tarefa(index, tarefa, usuario_logado, todas_tarefas):
    nome_tarefa = tarefa.get('titulo') or tarefa.get('nome') or f"Tarefa {tarefa.get('id', 'sem ID')}"
    
    st.subheader(f"Tarefa: {nome_tarefa}")
    if tarefa.get('Opção diária'):
        st.info("Esta é uma tarefa diária recorrente.")

    if tarefa.get('status') != "Aprovada":
        st.warning("Esta tarefa está pendente de aprovação.")
        return

    with st.expander("Detalhes da Execução"):
        if 'observacao_detalhada' in tarefa:
            st.write("Detalhes da Nota Fiscal:")
            st.text(tarefa['observacao_detalhada'])        
        if tarefa.get("status_execucao") != "Em Andamento":
            if st.button("Iniciar Tarefa", key=f"start_{index}"):
                tarefa['tempo_inicio'] = datetime.now().isoformat()
                tarefa['status_execucao'] = "Em Andamento"
                tarefa['Execução Membros'] = {membro: "Não Concluído" for membro in tarefa['Membros']}
                update_task_by_id(tarefa)
                st.rerun()
        else:
            tempo_inicio = datetime.fromisoformat(tarefa['tempo_inicio'])
            tempo_decorrido = datetime.now() - tempo_inicio
            st.write(f"Tempo decorrido: {tempo_decorrido}")

            comentario = st.text_area("Comentário sobre a execução", value="", key=f"comentario_{index}")
            
            uploaded_file = st.file_uploader("Anexar arquivo (opcional)", key=f"file_{index}")
            
            status_membro = st.selectbox(
                "Status da Execução Pessoal",
                ["Concluído", "Pendente", "Retorno"],
                key=f"status_membro_{index}"
            )
            
            if st.button("Salvar Progresso Pessoal", key=f"salvar_progresso_{index}"):
                nome_completo = next((membro for membro in tarefa['Membros'] if membro.split()[0] == usuario_logado.split()[0]), None)
                if nome_completo:
                    if status_membro == "Retorno":
                        sub_tarefa_id = criar_sub_tarefa_correcao(tarefa, nome_completo, comentario)
                        st.success(f"Sub-tarefa de correção criada com ID: {sub_tarefa_id}")
                        tarefa['status_execucao'] = "Aguardando Correção"
                    else:
                        tarefa['Execução Membros'][nome_completo] = status_membro
                    
                    if 'comentarios_execucao' not in tarefa:
                        tarefa['comentarios_execucao'] = {}
                    tarefa['comentarios_execucao'][nome_completo] = comentario
                                        
                    if uploaded_file is not None:
                        nome_pasta_tarefa = sanitize_filename(tarefa.get('titulo', f'tarefa_{index}'))
                        nome_subpasta = sanitize_filename(nome_completo)
                        
                        try:
                            # Criar pastas para a tarefa e para o membro
                            criar_pasta(f"Projeto1/{nome_pasta_tarefa}")
                            criar_pasta(f"Projeto1/{nome_pasta_tarefa}/{nome_subpasta}")
                            
                            nome_arquivo = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{sanitize_filename(uploaded_file.name)}"
                            caminho_completo = f"Projeto1/{nome_pasta_tarefa}/{nome_subpasta}/{nome_arquivo}"
                            
                            file_contents = uploaded_file.read()
                            
                            caminho_firebase = salvar_arquivo(caminho_completo, file_contents)
                            
                            if caminho_firebase:
                                if 'arquivos_membros' not in tarefa:
                                    tarefa['arquivos_membros'] = {}
                                tarefa['arquivos_membros'][nome_completo] = caminho_completo
                                st.success(f"Arquivo salvo com sucesso.")
                            else:
                                st.error("Falha ao salvar o arquivo.")
                        except Exception as e:
                            st.error(f"Erro ao processar o arquivo: {str(e)}")
                            time.sleep(5)

                    update_task_by_id(tarefa)
                    st.success(f"Progresso salvo para {nome_completo}.")
                    
                    if status_membro != "Retorno":
                        todos_concluidos = all(status == "Concluído" for status in tarefa['Execução Membros'].values())
                        if todos_concluidos:
                            tarefa["status_execucao"] = "Concluído"
                            
                            tempo_final = datetime.now()
                            tempo_total = tempo_final - tempo_inicio
                            tarefa['tempo_execucao'] = str(tempo_total)
                            tarefa['ultima_execucao'] = datetime.now().isoformat()
                            del tarefa['tempo_inicio']

                            update_task_by_id(tarefa)
                            st.success(f"Tarefa '{nome_tarefa}' finalizada com sucesso.")
                    
                    st.rerun()
                else:
                    st.error("Erro ao encontrar seu nome na lista de membros.")
                    
            st.write("Status atual dos membros:")
            for membro, status in tarefa['Execução Membros'].items():
                st.write(f"- {membro}: {status}")

            if tarefa.get('comentarios_execucao'):
                st.write("Comentários dos membros:")
                for membro, comentario in tarefa['comentarios_execucao'].items():
                    st.text(f"{membro}: {comentario}")

        if tarefa.get('arquivos_membros'):
            st.write("Arquivos anexados:")
            for membro, caminho_arquivo in tarefa['arquivos_membros'].items():
                arquivo_buffer = baixar_arquivo(caminho_arquivo)
                if arquivo_buffer:
                    nome_arquivo = os.path.basename(caminho_arquivo)
                    st.download_button(
                        label=f"Baixar arquivo de {membro}",
                        data=arquivo_buffer,
                        file_name=nome_arquivo,
                        mime="application/octet-stream",
                        key=f"download_{tarefa['id']}_{membro}"
                    )
                else:
                    st.warning(f"Não foi possível carregar o arquivo de {membro}")

            if tarefa["status_execucao"] != "Concluído":
                st.warning("A tarefa será finalizada automaticamente quando todos os membros concluírem suas partes.")
                membros_pendentes = [membro for membro, status in tarefa['Execução Membros'].items() if status != "Concluído"]
                if membros_pendentes:
                    st.write(f"Membros que ainda não concluíram: {', '.join(membros_pendentes)}")

def exibir_downloads(todas_tarefas, usuario_logado):
    st.header("Downloads de Arquivos")

    tarefas_relevantes = [
        t for t in todas_tarefas 
        if t.get("arquivos_membros") and 
           any(usuario_logado.split()[0] == membro.split()[0] for membro in t.get("Membros", []))
    ]

    if not tarefas_relevantes:
        st.info("Não há arquivos disponíveis para download nas suas tarefas.")
        return

    for tarefa in tarefas_relevantes:
        titulo_tarefa = tarefa.get('titulo') or f"Tarefa {tarefa.get('id', 'sem ID')}"
        st.subheader(f"Tarefa: {titulo_tarefa} (ID: {tarefa.get('id', 'N/A')})")
        
        for membro, caminho_arquivo in tarefa["arquivos_membros"].items():
            st.write(f"Arquivo de {membro}:")
            try:
                arquivo_buffer = baixar_arquivo(caminho_arquivo)
                file_contents = arquivo_buffer.getvalue()
                nome_arquivo = os.path.basename(caminho_arquivo)
                
                st.download_button(
                    label=f"Baixar arquivo de {membro}",
                    data=file_contents,
                    file_name=nome_arquivo,
                    mime="application/octet-stream",
                    key=f"download_{tarefa['id']}_{membro}"
                )
            except Exception as e:
                st.error(f"Erro ao processar o arquivo: {str(e)}")
                st.exception(e)
        
        if tarefa.get('comentarios_execucao'):
            st.write("Comentários dos membros:")
            for membro, comentario in tarefa['comentarios_execucao'].items():
                st.text(f"{membro}: {comentario}")
        
        st.write("---")  # Separador entre tarefas

if __name__ == "__main__":
    usuario_logado = "Nome do Usuário Logado"
    executar_tarefas(usuario_logado)