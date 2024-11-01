import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from Verificador import calcular_receitas

def developer_edit_mode():
    st.sidebar.header("Controles do Desenvolvedor")
    
    # Controle de tamanho de fonte
    font_size = st.sidebar.slider("Tamanho da Fonte", 10, 24, 16)
    st.markdown(f"""
    <style>
        .reportview-container .main .block-container{{
            font-size: {font_size}px;
        }}
    </style>
    """, unsafe_allow_html=True)

    # Controle de visibilidade dos elementos
    show_receita = st.sidebar.checkbox("Mostrar Receita Operacional", True)
    show_pedidos = st.sidebar.checkbox("Mostrar Quantidade de Pedidos", True)
    show_faturamento_7_dias = st.sidebar.checkbox("Mostrar Faturamento 7 Dias", True)
    show_distribuicao_clientes = st.sidebar.checkbox("Mostrar Distribuição de Clientes", True)
    show_metas = st.sidebar.checkbox("Mostrar Metas", True)

    # Controle de layout
    layout_metas = st.sidebar.radio("Layout das Metas", ["1 Coluna", "2 Colunas", "3 Colunas"])

    return show_receita, show_pedidos, show_faturamento_7_dias, show_distribuicao_clientes, show_metas, layout_metas

def main():
    st.title("Visão Geral do Faturamento")

    # Verificar se o usuário é desenvolvedor
    is_developer = st.session_state.get('user', {}).get('funcao') == 'Desenvolvedor'

    # Variáveis para controlar a visibilidade e layout
    show_receita = show_pedidos = show_faturamento_7_dias = show_distribuicao_clientes = show_metas = True
    layout_metas = "2 Colunas"

    # Botão para ativar o modo de edição (apenas visível para desenvolvedores)
    if is_developer:
        if st.sidebar.button("Ativar/Desativar Modo de Edição do Desenvolvedor"):
            st.session_state.edit_mode = not st.session_state.get('edit_mode', False)
        
        if st.session_state.get('edit_mode', False):
            st.sidebar.success("Modo de Edição Ativado")
            show_receita, show_pedidos, show_faturamento_7_dias, show_distribuicao_clientes, show_metas, layout_metas = developer_edit_mode()
        else:
            st.sidebar.info("Modo de Edição Desativado")

    st.write("Carregando dados...")

    try:
        resultados = calcular_receitas()
        st.write("Dados carregados com sucesso.")
    except Exception as e:
        st.error(f"Erro ao calcular receitas: {e}")
        return

    try:
        (receita_anual, receita_mensal, receita_diaria, receita_anterior, diferenca_receita, crescimento_receita,
         qtde_pedidos_atual, qtde_pedidos_anterior, diferenca_pedidos, crescimento_pedidos,
         faturamento_ultimos_sete_dias, tickets_por_mes_ano, distribuicao_clientes) = resultados
        st.write("Dados foram descompactados com sucesso.")
    except Exception as e:
        st.error(f"Erro ao descompactar resultados: {e}")
        return

    # Filtros de mês e ano
    st.sidebar.header("Filtros")
    meses = ["Todos"] + [str(i) for i in range(1, 13)]
    anos = ["Todos"] + sorted(set(str(ano) for ano, _, _, _, _ in tickets_por_mes_ano))
    mes_selecionado = st.sidebar.selectbox("Selecione o Mês", meses)
    ano_selecionado = st.sidebar.selectbox("Selecione o Ano", anos)

    # Converter filtros para uso na função
    mes_filtro = None if mes_selecionado == "Todos" else int(mes_selecionado)
    ano_filtro = None if ano_selecionado == "Todos" else int(ano_selecionado)

    # Verifique se há dados de tickets antes de continuar
    if not tickets_por_mes_ano:
        st.warning("Nenhum dado de tickets disponível.")
        return

    # Filtrar os tickets por mês e ano selecionados
    tickets_filtrados = filtrar_tickets(tickets_por_mes_ano, mes_filtro, ano_filtro)

    # Exibir cartões de Receita Operacional e Quantidade de Pedidos
    if show_receita or show_pedidos:
        exibir_cartoes_receita_pedidos(receita_anual, receita_mensal, receita_diaria, receita_anterior, diferenca_receita, crescimento_receita, qtde_pedidos_atual, qtde_pedidos_anterior, diferenca_pedidos, crescimento_pedidos, show_receita, show_pedidos)

    # Criar DataFrame para o gráfico de linha
    df_faturamento_7_dias = pd.DataFrame({
        'Data': [data for data, _ in faturamento_ultimos_sete_dias],
        'Faturamento': [faturamento for _, faturamento in faturamento_ultimos_sete_dias]
    })

    # Gráfico de linha do faturamento dos últimos 7 dias
    if show_faturamento_7_dias:
        exibir_grafico_faturamento_7_dias(df_faturamento_7_dias)

    # Gráfico de funil para distribuição de clientes por faixa de valor
    if show_distribuicao_clientes:
        exibir_grafico_funnel(distribuicao_clientes)

    # Atualizar dados para os gráficos de pizza
    metas = {
        "Meta Anual": (7.41, receita_anual / 1_000_000),  # Convertendo para milhões
        "Meta Mensal": (0.609, receita_mensal / 1_000_000),  # Convertendo para milhões
        "Meta Diária": (0.0275, receita_diaria / 1_000_000)  # Convertendo para milhões
    }

    # Gráficos de pizza
    if show_metas:
        exibir_graficos_pizza(metas, layout_metas)

def filtrar_tickets(tickets_por_mes_ano, mes_selecionado, ano_selecionado):
    if mes_selecionado is None:
        mes_selecionado = "Todos"
    if ano_selecionado is None:
        ano_selecionado = "Todos"

    if mes_selecionado == "Todos":
        if ano_selecionado == "Todos":
            tickets_anuais = {}
            for ano, mes, maximo, medio, minimo in tickets_por_mes_ano:
                if ano not in tickets_anuais:
                    tickets_anuais[ano] = {'max': [], 'med': [], 'min': []}
                tickets_anuais[ano]['max'].append(maximo)
                tickets_anuais[ano]['med'].append(medio)
                tickets_anuais[ano]['min'].append(minimo)
            tickets_filtrados = [(ano, max(tickets_anuais[ano]['max']), sum(tickets_anuais[ano]['med']) / len(tickets_anuais[ano]['med']), min(tickets_anuais[ano]['min'])) for ano in sorted(tickets_anuais.keys())]
        else:
            tickets_filtrados = [(ano, maximo, medio, minimo) for ano, mes, maximo, medio, minimo in tickets_por_mes_ano if ano == int(ano_selecionado)]
    else:
        mes_selecionado = int(mes_selecionado)
        if ano_selecionado == "Todos":
            tickets_anuais = {}
            for ano, mes, maximo, medio, minimo in tickets_por_mes_ano:
                if mes == mes_selecionado:
                    if ano not in tickets_anuais:
                        tickets_anuais[ano] = {'max': [], 'med': [], 'min': []}
                    tickets_anuais[ano]['max'].append(maximo)
                    tickets_anuais[ano]['med'].append(medio)
                    tickets_anuais[ano]['min'].append(minimo)
            tickets_filtrados = [(ano, max(tickets_anuais[ano]['max']), sum(tickets_anuais[ano]['med']) / len(tickets_anuais[ano]['med']), min(tickets_anuais[ano]['min'])) for ano in sorted(tickets_anuais.keys())]
        else:
            tickets_filtrados = [(ano, mes, maximo, medio, minimo) for ano, mes, maximo, medio, minimo in tickets_por_mes_ano if ano == int(ano_selecionado) and mes == mes_selecionado]
    return tickets_filtrados

def exibir_cartoes_receita_pedidos(receita_anual, receita_mensal, receita_diaria, receita_anterior, diferenca_receita, crescimento_receita, qtde_pedidos_atual, qtde_pedidos_anterior, diferenca_pedidos, crescimento_pedidos, show_receita, show_pedidos):
    if show_receita and show_pedidos:
        col1, col2 = st.columns(2)
    elif show_receita or show_pedidos:
        col1 = st.columns(1)[0]
    
    if show_receita:
        with col1:
            st.markdown("## Receita Operacional")
            st.markdown(f"### Valor Anual: {receita_anual / 1_000_000:.2f} Mi")
            st.markdown(f"### Valor Mensal: {receita_mensal / 1_000_000:.2f} Mi")
            st.markdown(f"### Valor Diário: {receita_diaria / 1_000_000:.2f} Mi")
            st.markdown(
                f"<span style='color:green; font-size:20px;'>Receita Anterior: {receita_anterior / 1_000_000:.2f} Mi, Diferença: {diferenca_receita / 1_000_000:.2f} Mi, Crescimento: {crescimento_receita:.2f}%</span>",
                unsafe_allow_html=True)

    if show_pedidos:
        with col2 if show_receita else col1:
            st.markdown("## Qtde de Pedidos", unsafe_allow_html=True)
            st.markdown(f"### Valor: {qtde_pedidos_atual}")
            st.markdown(
                f"<span style='color:green; font-size:20px;'>Anterior: {qtde_pedidos_anterior} Pedidos, Diferença: {diferenca_pedidos} Pedidos, Crescimento: {crescimento_pedidos:.2f}%</span>",
                unsafe_allow_html=True)

def exibir_grafico_faturamento_7_dias(df_faturamento_7_dias):
    if not df_faturamento_7_dias.empty:
        fig_line = px.line(df_faturamento_7_dias, x='Data', y='Faturamento', labels={'Faturamento': 'Faturamento (Mil)'}, title='Faturamento dos Últimos 7 Dias')
        fig_line.update_traces(line=dict(color='royalblue'))
        st.markdown("## Faturamento dos Últimos 7 Dias")
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.warning("Sem dados de faturamento para os últimos 7 dias.")

def exibir_grafico_funnel(distribuicao_clientes):
    if distribuicao_clientes:
        labels = [faixa for _, faixa in distribuicao_clientes]
        values = [count for count, _ in distribuicao_clientes]

        fig_funnel = go.Figure(go.Funnel(
            y=labels,
            x=values,
            textinfo="value+percent initial"))

        st.markdown("## Distribuição de Clientes por Faixa de Valor de Pedido")
        st.plotly_chart(fig_funnel, use_container_width=True)
    else:
        st.warning("Sem dados de distribuição de clientes.")

def exibir_graficos_pizza(metas, layout):
    st.markdown("## Metas")
    if layout == "1 Coluna":
        for meta, (valor_meta, valor_alcancado) in metas.items():
            fig_pie = go.Figure(data=[go.Pie(labels=['Alcançado', 'Meta'], values=[valor_alcancado, max(0, valor_meta - valor_alcancado)])])
            fig_pie.update_traces(hole=.4, hoverinfo="label+percent+name")
            fig_pie.update_layout(title_text=meta)
            st.plotly_chart(fig_pie, use_container_width=True)
    elif layout == "2 Colunas":
        col1, col2 = st.columns(2)
        for i, (meta, (valor_meta, valor_alcancado)) in enumerate(metas.items()):
            fig_pie = go.Figure(data=[go.Pie(labels=['Alcançado', 'Meta'], values=[valor_alcancado, max(0, valor_meta - valor_alcancado)])])
            fig_pie.update_traces(hole=.4, hoverinfo="label+percent+name")
            fig_pie.update_layout(title_text=meta)
            if i % 2 == 0:
                col1.plotly_chart(fig_pie, use_container_width=True)
            else:
                col2.plotly_chart(fig_pie, use_container_width=True)
    else:  # 3 Colunas
        col1, col2, col3 = st.columns(3)
        for i, (meta, (valor_meta, valor_alcancado)) in enumerate(metas.items()):
            fig_pie = go.Figure(data=[go.Pie(labels=['Alcançado', 'Meta'], values=[valor_alcancado, max(0, valor_meta - valor_alcancado)])])
            fig_pie.update_traces(hole=.4, hoverinfo="label+percent+name")
            fig_pie.update_layout(title_text=meta)
            if i % 3 == 0:
                col1.plotly_chart(fig_pie, use_container_width=True)
            elif i % 3 == 1:
                col2.plotly_chart(fig_pie, use_container_width=True)
            else:
                col3.plotly_chart(fig_pie, use_container_width=True)

if __name__ == "__main__":
    main()