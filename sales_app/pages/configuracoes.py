import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime

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

def main():
    # Configuração da página
    st.set_page_config(layout="wide")

    # Verificar se a senha foi inserida corretamente
    if check_password():
        st.sidebar.title("Configurações")
        x_pos = st.sidebar.slider("Posição X do Cartão", 0, 500, st.session_state.get("x_pos", 0))
        y_pos = st.sidebar.slider("Posição Y do Cartão", 0, 500, st.session_state.get("y_pos", 0))
        graph_size = st.sidebar.slider("Tamanho do Gráfico", 300, 800, st.session_state.get("graph_size", 600))
        
        if st.sidebar.button("Salvar Configurações"):
            save_config(x_pos, y_pos, graph_size)

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

if __name__ == "__main__":
    main()