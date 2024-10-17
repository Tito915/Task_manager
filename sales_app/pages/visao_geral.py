import sys
from pathlib import Path
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

# Adicionar o diretório 'pages' ao caminho do sistema
sys.path.append(str(Path(__file__).resolve().parent))

from Verificador import calcular_receitas  # Importar a função do Verificador.py

def main():
    st.title("Dashboard de Faturamento")

    # Obter o mês e o ano atuais
    mes_atual = datetime.now().month
    ano_atual = datetime.now().year

    # Obter dados calculados com base nos filtros (inicialmente sem filtros)
    resultados = calcular_receitas()
    (receita_anual, receita_mensal, receita_diaria, receita_anterior, diferenca_receita, crescimento_receita,
     qtde_pedidos_atual, qtde_pedidos_anterior, diferenca_pedidos, crescimento_pedidos,
     faturamento_ultimos_sete_dias, tickets_por_mes_ano, distribuicao_clientes) = resultados

    # Filtros de mês e ano
    st.sidebar.header("Filtros")
    meses = ["Todos"] + [str(i) for i in range(1, 13)]
    anos = ["Todos"] + sorted(set(str(ano) for ano, _, _, _, _ in tickets_por_mes_ano))
    mes_selecionado = st.sidebar.selectbox("Selecione o Mês", meses)
    ano_selecionado = st.sidebar.selectbox("Selecione o Ano", anos)

    # Converter filtros para uso na função
    mes_filtro = None if mes_selecionado == "Todos" else int(mes_selecionado)
    ano_filtro = None if ano_selecionado == "Todos" else int(ano_selecionado)

    # Obter dados calculados com base nos filtros
    resultados = calcular_receitas(mes_filtro, ano_filtro)
    (receita_anual, receita_mensal, receita_diaria, receita_anterior, diferenca_receita, crescimento_receita,
     qtde_pedidos_atual, qtde_pedidos_anterior, diferenca_pedidos, crescimento_pedidos,
     faturamento_ultimos_sete_dias, tickets_por_mes_ano, distribuicao_clientes) = resultados

    # Filtrar os tickets por mês e ano selecionados
    if mes_selecionado == "Todos":
        if ano_selecionado == "Todos":
            # Agregar por ano
            tickets_anuais = {}
            for ano, mes, maximo, medio, minimo in tickets_por_mes_ano:
                if ano not in tickets_anuais:
                    tickets_anuais[ano] = {'max': [], 'med': [], 'min': []}
                tickets_anuais[ano]['max'].append(maximo)
                tickets_anuais[ano]['med'].append(medio)
                tickets_anuais[ano]['min'].append(minimo)
            tickets_filtrados = [(ano, max(tickets_anuais[ano]['max']), sum(tickets_anuais[ano]['med']) / len(tickets_anuais[ano]['med']), min(tickets_anuais[ano]['min'])) for ano in sorted(tickets_anuais.keys())]
        else:
            # Agregar por ano específico
            tickets_filtrados = [(ano, maximo, medio, minimo) for ano, mes, maximo, medio, minimo in tickets_por_mes_ano if ano == int(ano_selecionado)]
    else:
        mes_selecionado = int(mes_selecionado)
        if ano_selecionado == "Todos":
            # Agregar por ano
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

    # Exibir cartões de Receita Operacional e Quantidade de Pedidos
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("## Receita Operacional")
        st.markdown(f"### Valor Anual: {receita_anual / 1_000_000:.2f} Mi")
        st.markdown(f"### Valor Mensal: {receita_mensal / 1_000_000:.2f} Mi")
        st.markdown(f"### Valor Diário: {receita_diaria / 1_000_000:.2f} Mi")
        st.markdown(
            f"<span style='color:green; font-size:20px;'>Receita Anterior: {receita_anterior / 1_000_000:.2f} Mi, Diferença: {diferenca_receita / 1_000_000:.2f} Mi, Crescimento: {crescimento_receita:.2f}%</span>",
            unsafe_allow_html=True)

    with col2:
        st.markdown("## Qtde de Pedidos", unsafe_allow_html=True)
        st.markdown(f"### Valor: {qtde_pedidos_atual}")
        st.markdown(
            f"<span style='color:green; font-size:20px;'>Anterior: {qtde_pedidos_anterior} Pedidos, Diferença: {diferenca_pedidos} Pedidos, Crescimento: {crescimento_pedidos:.2f}%</span>",
            unsafe_allow_html=True)

    # Exibir tickets no lado direito
    with col3:
        st.markdown("## Tickets por Ano")
        for ano, maximo, medio, minimo in tickets_filtrados:
            st.markdown(f"### Ano: {int(ano)}")
            st.markdown(f"<span style='color:green; font-size:20px;'>Ticket Máximo: R$ {maximo:.2f}</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:yellow; font-size:20px;'>Ticket Médio: R$ {medio:.2f}</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:red; font-size:20px;'>Ticket Mínimo: R$ {minimo:.2f}</span>", unsafe_allow_html=True)

    # Criar DataFrame para o gráfico de linha
    df_faturamento_7_dias = pd.DataFrame({
        'Data': [data for data, _ in faturamento_ultimos_sete_dias],
        'Faturamento': [faturamento for _, faturamento in faturamento_ultimos_sete_dias]
    })

    # Gráfico de linha do faturamento dos últimos 7 dias
    fig_line = px.line(df_faturamento_7_dias, x='Data', y='Faturamento', labels={'Faturamento': 'Faturamento (Mil)'}, title='Faturamento dos Últimos 7 Dias')
    fig_line.update_traces(line=dict(color='royalblue'))
    st.markdown("## Faturamento dos Últimos 7 Dias")
    st.plotly_chart(fig_line, use_container_width=True)

    # Gráfico de funil para distribuição de clientes por faixa de valor
    labels = [faixa for _, faixa in distribuicao_clientes]
    values = [count for count, _ in distribuicao_clientes]

    fig_funnel = go.Figure(go.Funnel(
        y=labels,
        x=values,
        textinfo="value+percent initial"))

    st.markdown("## Distribuição de Clientes por Faixa de Valor de Pedido")
    st.plotly_chart(fig_funnel, use_container_width=True)

    # Atualizar dados para os gráficos de pizza
    metas = {
        "Meta Anual": (7.41, receita_anual / 1_000_000),  # Convertendo para milhões
        "Meta Mensal": (0.609, receita_mensal / 1_000_000),  # Convertendo para milhões
        "Meta Diária": (0.0275, receita_diaria / 1_000_000)  # Convertendo para milhões
    }

    # Gráficos de pizza
    st.markdown("## Metas")
    col1, col2 = st.columns(2)
    for i, (meta, (valor_meta, valor_alcancado)) in enumerate(metas.items()):
        fig_pie = go.Figure(data=[go.Pie(labels=['Alcançado', 'Meta'], values=[valor_alcancado, max(0, valor_meta - valor_alcancado)])])
        fig_pie.update_traces(hole=.4, hoverinfo="label+percent+name")
        fig_pie.update_layout(title_text=meta)
        if i % 2 == 0:
            col1.plotly_chart(fig_pie, use_container_width=True)
        else:
            col2.plotly_chart(fig_pie, use_container_width=True)

if __name__ == "__main__":
    main()