import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime

def check_environment():
    return st.session_state.get('ambiente', 'Task Manager')

def check_password():
    def password_entered():
        if st.session_state["password"] == "Ermec6sello*":
            st.session_state["authenticated"] = True
            del st.session_state["password"]  # Remove o campo de senha
        else:
            st.session_state["authenticated"] = False

    if "authenticated" not in st.session_state:
        # Solicitar senha
        st.text_input("Senha do desenvolvedor", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["authenticated"]:
        st.text_input("Senha do desenvolvedor", type="password", on_change=password_entered, key="password")
        st.error("Senha incorreta")
        return False
    else:
        return True

def save_config(x_pos, y_pos, graph_size):
    st.session_state["x_pos"] = x_pos
    st.session_state["y_pos"] = y_pos
    st.session_state["graph_size"] = graph_size

def main(ambiente):
    if ambiente != "Sales App":
        st.error("Esta página só está disponível no ambiente Sales App.")
        return

    # Configuração da página
    st.set_page_config(layout="wide")

    st.title("Configurações")

    # Verificar se a senha foi inserida corretamente
    if check_password():
        st.sidebar.header("Ajustes")
        x_pos = st.sidebar.slider("Posição X do Cartão", 0, 500, st.session_state.get("x_pos", 0))
        y_pos = st.sidebar.slider("Posição Y do Cartão", 0, 500, st.session_state.get("y_pos", 0))
        graph_size = st.sidebar.slider("Tamanho do Gráfico", 300, 800, st.session_state.get("graph_size", 600))
        
        if st.sidebar.button("Salvar Configurações"):
            save_config(x_pos, y_pos, graph_size)
            st.sidebar.success("Configurações salvas com sucesso!")

        # Exibir cartão com posição ajustável
        st.markdown(f"""
        <div style="position: absolute; left: {x_pos}px; top: {y_pos}px;">
            <div style="background-color: lightgrey; padding: 10px; border-radius: 5px;">
                <h4>Cartão Personalizado</h4>
                <p>Conteúdo do cartão</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Exibir gráfico com tamanho ajustável
        df = pd.DataFrame({'x': range(10), 'y': range(10)})
        fig = px.line(df, x='x', y='y', title='Gráfico Exemplo')
        fig.update_layout(width=graph_size, height=graph_size)
        st.plotly_chart(fig)

        # Adicionar mais opções de configuração
        st.header("Opções Adicionais")
        
        # Exemplo de configuração de cores
        color_scheme = st.selectbox("Esquema de Cores", ["Padrão", "Escuro", "Claro"])
        st.session_state["color_scheme"] = color_scheme
        
        # Exemplo de configuração de fonte
        font_size = st.slider("Tamanho da Fonte", 10, 24, st.session_state.get("font_size", 16))
        st.session_state["font_size"] = font_size
        
        # Exemplo de configuração de atualização automática
        auto_refresh = st.checkbox("Atualização Automática", value=st.session_state.get("auto_refresh", False))
        st.session_state["auto_refresh"] = auto_refresh
        
        if auto_refresh:
            refresh_interval = st.number_input("Intervalo de Atualização (segundos)", min_value=5, value=st.session_state.get("refresh_interval", 60))
            st.session_state["refresh_interval"] = refresh_interval

        # Botão para resetar todas as configurações
        if st.button("Resetar Todas as Configurações"):
            for key in ["x_pos", "y_pos", "graph_size", "color_scheme", "font_size", "auto_refresh", "refresh_interval"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.success("Todas as configurações foram resetadas para os valores padrão.")
            st.experimental_rerun()

    else:
        st.warning("Por favor, insira a senha correta para acessar as configurações.")

if __name__ == "__main__":
    ambiente = check_environment()
    main(ambiente)