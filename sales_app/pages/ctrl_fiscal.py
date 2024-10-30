import streamlit as st
import plotly.express as px
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

# Configuração da página deve ser a primeira chamada Streamlit
st.set_page_config(layout="wide")

# Adicione o diretório 'pages' ao caminho do sistema
sys.path.append(str(Path(__file__).resolve().parent.parent))

from Dados_Controle_Ctrl_Fiscal import obter_faturamento_anual_todos, obter_faturamento_mensal_todos, obter_faturamento_por_natureza, obter_entradas_mensais

def carregar_dados():
    """Função para carregar dados com tratamento de erros."""
    try:
        faturamento_anual = obter_faturamento_anual_todos()
        faturamento_mensal = obter_faturamento_mensal_todos()
        entradas_mensais = obter_entradas_mensais()

        faturamento_anual = [(int(ano), float(valor)) for ano, valor in faturamento_anual]
        faturamento_mensal = [(int(ano), int(mes), float(valor)) for ano, mes, valor in faturamento_mensal]

        return faturamento_anual, faturamento_mensal, entradas_mensais
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None, None, None

def main():
    # Título da página
    st.title("Controle Fiscal")

    # Botão para atualizar dados
    if st.button("Atualizar Dados"):
        st.session_state['atualizar'] = True
    else:
        st.session_state['atualizar'] = False

    # Carregar dados apenas se o botão for pressionado
    if st.session_state.get('atualizar', True):
        try:
            faturamento_anual, faturamento_mensal, entradas_mensais = carregar_dados()
            if faturamento_anual is None or faturamento_mensal is None or entradas_mensais is None:
                st.error("Erro ao carregar dados.")
                return
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
            return

        # Criar DataFrame para visualização do faturamento anual
        df_anual = pd.DataFrame(faturamento_anual, columns=['Ano', 'Faturamento Anual'])

        # Layout principal
        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("### Faturamento Anual")
            for ano, valor in faturamento_anual:
                st.metric(label=f"Faturamento {ano}", value=f"R$ {valor / 1_000_000:,.2f} Mi")

            # Tabela de Faturamento Mensal
            st.markdown("### Faturamento Mensal")
            df_mensal = pd.DataFrame(faturamento_mensal, columns=['Ano', 'Mês', 'Faturamento Mensal'])
            df_mensal['Data'] = pd.to_datetime(df_mensal['Ano'].astype(str) + '-' + df_mensal['Mês'].astype(str) + '-01')
            df_mensal['Mês/Ano'] = df_mensal['Data'].dt.strftime('%b/%Y')
            df_mensal['Faturamento'] = df_mensal['Faturamento Mensal'].apply(lambda x: f"R$ {x/1000:,.2f} Mil")
            df_mensal_display = df_mensal[['Data', 'Mês/Ano', 'Faturamento']].sort_values('Data', ascending=False)
            st.dataframe(df_mensal_display[['Mês/Ano', 'Faturamento']], width=300, height=300)

        with col2:
            # Calcular metas e teto de faturamento
            ano_atual = datetime.now().year
            mes_atual = datetime.now().month

            # Filtrar dados do ano atual
            df_ano_atual = df_mensal[df_mensal['Ano'] == ano_atual]

            # Calcular faturamento acumulado
            faturamento_acumulado = df_ano_atual['Faturamento Mensal'].sum()

            # Calcular número de meses restantes
            meses_restantes = 12 - mes_atual + 1  # +1 para incluir o mês atual

            # Calcular valor disponível para faturamento
            limite_anual = 3_600_000  # 3,6 milhões
            valor_disponivel = max(0, limite_anual - faturamento_acumulado)

            # Calcular teto mensal
            teto_mensal = valor_disponivel / meses_restantes if meses_restantes > 0 else 0

            # Calcular média de faturamento dos meses anteriores
            media_faturamento = faturamento_acumulado / (mes_atual - 1) if mes_atual > 1 else faturamento_acumulado

            # Obter faturamento do último mês
            ultimo_faturamento = df_ano_atual[df_ano_atual['Mês'] == mes_atual]['Faturamento Mensal'].values[0] if mes_atual > 1 else 0

            # Obter faturamento por natureza do mês atual
            faturamento_por_natureza_atual = obter_faturamento_por_natureza(ano_atual, mes_atual)

            # Calcular o faturamento com cartão
            faturamento_cartao = sum(valor for natureza, valor in faturamento_por_natureza_atual if natureza.lower() == "venda com cartão")

            # Calcular a meta de cartão (200% do faturamento com cartão)
            meta_cartao = faturamento_cartao * 2

            # Obter o valor de entrada do mês atual
            valor_entrada = next((valor for ano, mes, valor in entradas_mensais if ano == ano_atual and mes == mes_atual), 0)
            meta_135 = 1.35 * valor_entrada

            st.markdown("### Metas e Teto de Faturamento")
            col2_1, col2_2, col2_3 = st.columns(3)
            with col2_1:
                st.metric(label="Faturamento Acumulado", value=f"R$ {faturamento_acumulado / 1_000_000:,.2f} Mi")
            with col2_2:
                st.metric(label="Teto Mensal", value=f"R$ {teto_mensal / 1_000:,.2f} Mil")
            with col2_3:
                st.metric(label="Valor Disponível", value=f"R$ {valor_disponivel / 1_000_000:,.2f} Mi")

            st.markdown("### Metas")
            col2_4, col2_5, col2_6 = st.columns(3)
            with col2_4:
                st.metric(label="Faturamento Mês Atual", value=f"R$ {ultimo_faturamento / 1_000:,.2f} Mil")
            with col2_5:
                st.metric(label="1ª Meta Cartão (200%)", value=f"R$ {meta_cartao / 1_000:,.2f} Mil")
            with col2_6:
                st.metric(label="2ª Meta 135% da Entrada", value=f"R$ {meta_135 / 1_000:,.2f} Mil")

            st.info(f"Valor de entrada do mês atual: R$ {valor_entrada / 1_000:,.2f} Mil")
            st.info(f"Média de faturamento mensal: R$ {media_faturamento / 1_000:,.2f} Mil")

            # Alerta se o teto mensal for menor que a média ou o último faturamento
            if teto_mensal < media_faturamento or teto_mensal < ultimo_faturamento:
                st.warning("Atenção: O teto mensal está abaixo da média de faturamento ou do último faturamento. Ajuste o faturamento para não ultrapassar o limite anual.")

            # Gráfico de Faturamento Anual por Ano
            fig_anual = px.bar(df_anual, x='Ano', y='Faturamento Anual', title='Faturamento Anual por Ano', labels={'Faturamento Anual': 'Valor (R$)'})
            fig_anual.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_anual, use_container_width=True)

        # Adiciona filtros de ano e mês na barra lateral
        st.sidebar.header("Filtros")
        anos_disponiveis = sorted(df_anual['Ano'].unique())
        meses_disponiveis = list(range(1, 13))

        ano_selecionado = st.sidebar.selectbox("Selecione o Ano", anos_disponiveis, index=0 if datetime.now().year not in anos_disponiveis else anos_disponiveis.index(datetime.now().year))
        mes_selecionado = st.sidebar.selectbox("Selecione o Mês", meses_disponiveis, index=datetime.now().month - 1)

        ano_selecionado = int(ano_selecionado)
        mes_selecionado = int(mes_selecionado)

        # Obter dados específicos para o ano e mês selecionados
        faturamento_por_natureza = obter_faturamento_por_natureza(ano_selecionado, mes_selecionado)

        # Criar DataFrame para visualização do faturamento por natureza
        df_natureza_venda = pd.DataFrame(faturamento_por_natureza, columns=['Natureza', 'Valor'])

        # Gráfico de barras para Faturamento por Natureza
        st.markdown("### Faturamento por Natureza")
        fig_barras = px.bar(df_natureza_venda, x='Natureza', y='Valor', title=f'Faturamento por Natureza - {mes_selecionado}/{ano_selecionado}', labels={'Valor': 'Valor (R$)'})
        fig_barras.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_barras, use_container_width=True)

        # Exibir o valor de "venda com cartão" usado para o cálculo da meta
        st.info(f"Valor de 'Venda com Cartão' usado para cálculo da meta: R$ {faturamento_cartao / 1_000:,.2f} Mil")

        # Gráfico de barras para Entradas Mensais do ano atual
        st.markdown("### Entradas Mensais")
        
        # Filtrar entradas do ano atual
        entradas_ano_atual = [(mes, valor) for ano, mes, valor in entradas_mensais if ano == ano_atual]
        
        if entradas_ano_atual:
            # Criar DataFrame para as entradas do ano atual
            df_entradas = pd.DataFrame(entradas_ano_atual, columns=['Mês', 'Valor'])
            df_entradas['Mês'] = df_entradas['Mês'].apply(lambda x: datetime(ano_atual, x, 1).strftime('%b'))  # Converter número do mês para nome abreviado
            
            # Criar gráfico de barras para entradas mensais
            fig_entradas = px.bar(df_entradas, x='Mês', y='Valor', 
                                  title=f'Entradas Mensais - {ano_atual}',
                                  labels={'Valor': 'Valor (R$)', 'Mês': 'Mês'},
                                  text='Valor')  # Adiciona o valor em cada barra
            
            # Personalizar o layout do gráfico
            fig_entradas.update_traces(texttemplate='R$ %{text:.2f}', textposition='outside')
            fig_entradas.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
            fig_entradas.update_yaxes(title='Valor (R$)')
            
            # Exibir o gráfico
            st.plotly_chart(fig_entradas, use_container_width=True)
        else:
            st.warning(f"Não há dados de entradas para o ano {ano_atual}.")

if __name__ == "__main__":
    main()