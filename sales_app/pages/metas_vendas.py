import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from ..Dados_MetasVendas import calcular_faturamento_bruto, calcular_fld, obter_vendas_diarias, obter_vendedores, obter_maiores_faturamentos
import json
import os

# Caminho para o arquivo de configurações
CONFIG_FILE = 'dev_settings_metas_vendas.json'

def load_dev_settings():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return None

def save_dev_settings(settings):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(settings, f)

def init_session_state():
    if 'dev_settings' not in st.session_state:
        default_settings = {
            'font_size': 16,
            'show_faturamento_anual': True,
            'show_faturamento_mensal': True,
            'show_faturamento_diario': True,
            'show_budget': True,
            'show_vendas_diarias': True,
            'show_metas_vendedores': True,
            'show_ranking_clientes': True
        }
        
        saved_settings = load_dev_settings()
        if saved_settings:
            default_settings.update(saved_settings)
        
        st.session_state.dev_settings = default_settings
    
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False

def developer_edit_mode():
    st.sidebar.header("Controles do Desenvolvedor")
    
    for key in st.session_state.dev_settings:
        if key == 'font_size':
            st.session_state.dev_settings[key] = st.sidebar.slider("Tamanho da Fonte", 10, 24, st.session_state.dev_settings[key])
        else:
            st.session_state.dev_settings[key] = st.sidebar.checkbox(f"Mostrar {key.replace('_', ' ').title()}", st.session_state.dev_settings[key])

    if st.sidebar.button("Salvar Configurações"):
        save_dev_settings(st.session_state.dev_settings)
        st.success("Configurações salvas com sucesso!")

def create_metric_card(title, value, subtitle=None, percentage=None):
    percentage_html = f'<span style="color: {"green" if percentage >= 100 else "red"}; font-size: 18px;"> ({percentage:.1f}%)</span>' if percentage is not None else ''
    html = f"""
    <div style="
        background-color: #ffffff;
        border: 1px solid #ddd;
        padding: 10px;
        border-radius: 5px;
        height: 100px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    ">
        <h3 style="color: #333; font-size: 14px; margin-bottom: 5px;">{title}</h3>
        <p style="color: #0066cc; font-size: 24px; font-weight: bold; margin: 0;">{value} {percentage_html}</p>
        {f'<p style="color: #666; font-size: 12px; margin-top: 5px;">{subtitle}</p>' if subtitle else ''}
    </div>
    """
    return st.markdown(html, unsafe_allow_html=True)

@st.cache_data
def load_faturamento(ano, mes=None, dia=None):
    fat_bruto = calcular_faturamento_bruto(ano=ano, mes=mes, dia=dia)
    fld = calcular_fld(ano=ano, mes=mes, dia=dia)
    return fat_bruto, fld

@st.cache_data
def load_vendas_diarias(ano, mes, vendedores):
    return obter_vendas_diarias(ano=ano, mes=mes, vendedores=vendedores)

@st.cache_data
def load_maiores_faturamentos(ano, mes, limite):
    return obter_maiores_faturamentos(ano=ano, mes=mes, limite=limite)

def main():
    init_session_state()
    st.title("Metas de Vendas")
    
    # Cria o arquivo de configurações se não existir
    if not os.path.exists(CONFIG_FILE):
        save_dev_settings(st.session_state.dev_settings)
    
    # Verificar se o usuário é desenvolvedor
    is_developer = st.session_state.get('user', {}).get('funcao') == 'Desenvolvedor'

    if is_developer:
        if st.sidebar.button("Ativar/Desativar Modo de Edição do Desenvolvedor"):
            st.session_state.edit_mode = not st.session_state.edit_mode
        
        if st.session_state.edit_mode:
            st.sidebar.success("Modo de Edição Ativado")
            developer_edit_mode()
        else:
            st.sidebar.info("Modo de Edição Desativado")

    # Aplicar tamanho de fonte
    st.markdown(f"""
    <style>
        .reportview-container .main .block-container{{
            font-size: {st.session_state.dev_settings.get('font_size', 16)}px;
        }}
    </style>
    """, unsafe_allow_html=True)

    if st.button("Atualizar Dados"):
        st.session_state['atualizar'] = True
    else:
        st.session_state['atualizar'] = False

    if st.session_state.get('atualizar', True):
        try:
            todos_vendedores = obter_vendedores()
            if not todos_vendedores:
                st.warning("Não foi possível obter a lista de vendedores.")
                return
        except Exception as e:
            st.error(f"Erro ao obter vendedores: {e}")
            return

        ano_padrao = datetime.now().year
        mes_padrao = datetime.now().month
        vendedores_padrao = ["Marcos", "Penha"]

        vendedor_selecionado = st.sidebar.multiselect("Selecione o Vendedor", todos_vendedores, default=vendedores_padrao)

        anos = ["Todos", 2024, 2023]
        meses = ["Todos"] + list(range(1, 13))
        ano_selecionado = st.sidebar.selectbox("Selecione o Ano", anos, index=anos.index(ano_padrao))
        mes_selecionado = st.sidebar.selectbox("Selecione o Mês", meses, index=meses.index(mes_padrao))

        ano = None if ano_selecionado == "Todos" else int(ano_selecionado)
        mes = None if mes_selecionado == "Todos" else int(mes_selecionado)

        try:
            fat_bruto_anual, fld_anual = load_faturamento(ano)
            fat_bruto_mensal, fld_mensal = load_faturamento(ano, mes)
            dia_atual = datetime.now().day
            fat_bruto_diario, fld_diario = load_faturamento(ano, mes, dia_atual)
        except Exception as e:
            st.error(f"Erro ao calcular faturamento: {e}")
            return

        percentual_desconto_anual = ((fat_bruto_anual - fld_anual) / fat_bruto_anual) * 100 if fat_bruto_anual else 0
        percentual_desconto_mensal = ((fat_bruto_mensal - fld_mensal) / fat_bruto_mensal) * 100 if fat_bruto_mensal else 0
        percentual_desconto_diario = ((fat_bruto_diario - fld_diario) / fat_bruto_diario) * 100 if fat_bruto_diario else 0

        budget_mensal = 609790
        budget_anual = 7270000
        budget_diario = 27000

        diferenca_anual = budget_anual - fat_bruto_anual
        previsao_mensal = (fat_bruto_mensal / budget_mensal) * 100 if budget_mensal else 0

        percentual_fld_anual = (fld_anual / budget_anual) * 100 if budget_anual else 0
        percentual_fld_mensal = (fld_mensal / budget_mensal) * 100 if budget_mensal else 0
        percentual_fld_diario = (fld_diario / budget_diario) * 100 if budget_diario else 0

        if st.session_state.dev_settings.get('show_faturamento_anual', True):
            st.markdown("### Faturamento Anual")
            col1, col2, col3 = st.columns(3)
            with col1:
                create_metric_card("Fat. Bruto Anual", f"R$ {fat_bruto_anual / 1_000_000:,.2f} Mi")
            with col2:
                create_metric_card("FLD Anual", f"R$ {fld_anual / 1_000_000:,.2f} Mi", percentage=percentual_fld_anual)
            with col3:
                create_metric_card("Percentual de Desconto Anual", f"{percentual_desconto_anual:.2f}%")

        if st.session_state.dev_settings.get('show_faturamento_mensal', True):
            st.markdown("### Faturamento Mensal")
            col1, col2, col3 = st.columns(3)
            with col1:
                create_metric_card("Fat. Bruto Mensal", f"R$ {fat_bruto_mensal / 1_000:,.2f} Mil")
            with col2:
                create_metric_card("FLD Mensal", f"R$ {fld_mensal / 1_000:,.2f} Mil", percentage=percentual_fld_mensal)
            with col3:
                create_metric_card("Desconto Mensal", f"{percentual_desconto_mensal:.2f}%")

        if st.session_state.dev_settings.get('show_faturamento_diario', True):
            st.markdown("### Faturamento Diário")
            col1, col2, col3 = st.columns(3)
            with col1:
                create_metric_card("Fat. Bruto Diário", f"R$ {fat_bruto_diario / 1_000:,.2f} Mil")
            with col2:
                create_metric_card("FLD Diário", f"R$ {fld_diario / 1_000:,.2f} Mil", percentage=percentual_fld_diario)
            with col3:
                create_metric_card("Desconto Diário", f"{percentual_desconto_diario:.2f}%")

        if st.session_state.dev_settings.get('show_budget', True):
            st.markdown("### Budget")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                create_metric_card("Meta Mensal", f"R$ {budget_mensal / 1_000:,.2f} Mil")
            with col2:
                create_metric_card("Meta Anual", f"R$ {budget_anual / 1_000_000:,.2f} Mi")
            with col3:
                create_metric_card("Diferença para Meta Anual", f"R$ {diferenca_anual / 1_000_000:,.2f} Mi")
            with col4:
                create_metric_card("Previsão Mensal (%)", f"{previsao_mensal:.2f}%")

        if st.session_state.dev_settings.get('show_vendas_diarias', True):
            try:
                vendas_diarias = load_vendas_diarias(ano, mes, vendedor_selecionado)
                if vendas_diarias:
                    df_vendas_diarias = pd.DataFrame(vendas_diarias, columns=['data', 'vendedor', 'vendas_diarias'])
                    
                    fig_line = px.line(df_vendas_diarias, x='data', y='vendas_diarias', color='vendedor',
                                       labels={'vendas_diarias': 'Vendas Diárias (Mil)', 'data': 'Data'},
                                       title='Vendas Diárias por Vendedor')

                    df_vendas_diarias['vendas_diarias_format'] = df_vendas_diarias['vendas_diarias'] / 1_000
                    fig_line.update_traces(mode='lines+markers+text', text=df_vendas_diarias['vendas_diarias_format'].apply(lambda x: f"{x:,.2f} Mil"), textposition='top center')
                    st.plotly_chart(fig_line, use_container_width=True)
                else:
                    st.warning("Não há dados de vendas diárias para o período selecionado.")
            except Exception as e:
                st.error(f"Erro ao carregar vendas diárias: {e}")

        if st.session_state.dev_settings.get('show_metas_vendedores', True) or st.session_state.dev_settings.get('show_ranking_clientes', True):
            try:
                fld_por_vendedor = {vendedor: calcular_fld(ano=ano, mes=mes, vendedor=vendedor) for vendedor in todos_vendedores}
                vendedores_com_movimento = [vendedor for vendedor, fld in fld_por_vendedor.items() if fld > 0]

                meta_por_vendedor = 304890

                if vendedores_com_movimento:
                    df_metas = pd.DataFrame({
                        "Vendedor": vendedores_com_movimento,
                        "Meta": [meta_por_vendedor] * len(vendedores_com_movimento),
                        "Alcançado": [fld_por_vendedor[vendedor] for vendedor in vendedores_com_movimento]
                    })

                    col1, col2 = st.columns(2)

                    if st.session_state.dev_settings['show_metas_vendedores']:
                        with col1:
                            fig_bar = go.Figure()
                            fig_bar.add_trace(go.Bar(
                                y=df_metas['Vendedor'],
                                x=df_metas['Meta'],
                                name='Meta',
                                orientation='h',
                                marker=dict(color='lightgray')
                            ))
                            fig_bar.add_trace(go.Bar(
                                y=df_metas['Vendedor'],
                                x=df_metas['Alcançado'],
                                name='Alcançado',
                                orientation='h',
                                marker=dict(color=['blue', 'darkorange'])
                            ))

                            fig_bar.update_layout(barmode='overlay', title='Meta Mensal vs Alcançado por Vendedor')
                            st.plotly_chart(fig_bar, use_container_width=True)

                    if st.session_state.dev_settings['show_ranking_clientes']:
                        with col2:
                            st.markdown("### Ranking dos 20 Maiores Faturamentos de Clientes")
                            maiores_faturamentos = load_maiores_faturamentos(ano, mes, 20)
                            if maiores_faturamentos:
                                df_clientes = pd.DataFrame(maiores_faturamentos, columns=['Cliente', 'FLD'])
                                st.dataframe(df_clientes)
                else:
                    st.warning("Não há dados de FLD por vendedor para o período selecionado.")
            except Exception as e:
                st.error(f"Erro ao calcular FLD por vendedor: {e}")

if __name__ == "__main__":
    main()