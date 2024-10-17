import streamlit as st
import pandas as pd
import json
from datetime import datetime

def load_tasks():
    try:
        # Alterado para usar um caminho relativo
        with open("tasks.json", "r", encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def home_page():
    st.title("Task App - Grupo MBV")

    # Carregar tarefas do arquivo JSON
    tarefas = load_tasks()

    # Converter para DataFrame
    df_tarefas = pd.DataFrame(tarefas)

    # Função para verificar se uma tarefa está em atraso
    def is_atrasada(tarefa):
        if tarefa.get('Data Fim'):
            data_fim = datetime.strptime(tarefa['Data Fim'], "%Y-%m-%d").date()
            return data_fim < datetime.now().date() and tarefa.get('status_execucao') != "Concluído"
        return False

    # Calcular métricas
    total_tarefas = len(tarefas)
    tarefas_concluidas = sum(1 for t in tarefas if t.get('status_execucao') == "Concluído")
    tarefas_atrasadas = sum(1 for t in tarefas if is_atrasada(t))
    tarefas_canceladas = sum(1 for t in tarefas if t.get('status') == "Cancelada")
    
    # Novas métricas para retornos e correções
    tarefas_em_correcao = sum(1 for t in tarefas if t.get('status_execucao') == "Aguardando Correção")
    total_retornos = sum(len([s for s in t.get('Execução Membros', {}).values() if s == "Retorno"]) for t in tarefas)

    # Criando colunas para os cartões de resumo
    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)

    # Cartões de resumo
    with col1:
        st.metric("Qtde de Tarefas Criadas", total_tarefas)
    
    with col2:
        st.metric("Qtde de Tarefas Executadas", tarefas_concluidas)
    
    with col3:
        st.metric("Qtde de Tarefas em Atraso", tarefas_atrasadas)
    
    with col4:
        st.metric("Qtde de Tarefas Canceladas", tarefas_canceladas)
    
    with col5:
        st.metric("Tarefas em Correção", tarefas_em_correcao)
    
    with col6:
        st.metric("Total de Retornos", total_retornos)

    # Gráfico de barras para status das tarefas
    if not df_tarefas.empty and 'status_execucao' in df_tarefas.columns:
        status_counts = df_tarefas['status_execucao'].value_counts()
        st.subheader("Distribuição de Status das Tarefas")
        st.bar_chart(status_counts)
    else:
        st.write("Não há dados suficientes para gerar o gráfico de status.")

    # Gráfico de pizza para distribuição de retornos por departamento
    if not df_tarefas.empty and 'Departamento' in df_tarefas.columns:
        retornos_por_departamento = df_tarefas.groupby('Departamento').apply(
            lambda x: sum(len([s for s in t.get('Execução Membros', {}).values() if s == "Retorno"]) for t in x.to_dict('records'))
        )
        st.subheader("Distribuição de Retornos por Departamento")
        st.pie_chart(retornos_por_departamento)

    # Tabela com as últimas tarefas criadas
    if not df_tarefas.empty:
        st.subheader("Últimas Tarefas Criadas")
        ultimas_tarefas = df_tarefas.sort_values('id', ascending=False).head(5)
        
        # Selecionar colunas disponíveis
        colunas_disponiveis = ['titulo', 'status_execucao', 'Departamento']
        if 'Data Início' in df_tarefas.columns:
            colunas_disponiveis.append('Data Início')
        elif 'Data InÃ\xadcio' in df_tarefas.columns:  # Verificar se há uma versão codificada do nome da coluna
            colunas_disponiveis.append('Data InÃ\xadcio')
        
        st.table(ultimas_tarefas[colunas_disponiveis])
    else:
        st.write("Não há tarefas para exibir.")

    # Exibir todas as colunas disponíveis (para debug)
    st.subheader("Colunas disponíveis no DataFrame:")
    st.write(df_tarefas.columns.tolist())

if __name__ == "__main__":
    home_page()