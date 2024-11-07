import streamlit as st
from utils import get_user_permissions

def home():
    user_permissions = get_user_permissions(st.session_state.user['email'])
    if "ver_home" in user_permissions:
        st.title("Página Inicial")
        # Código da página inicial
    else:
        st.warning("Você não tem permissão para acessar esta página.")

# Inicializar session_state se não existir
if 'dados' not in st.session_state:
    st.session_state['dados'] = {
        'df_vendas': None  # Inicialize com None ou carregue seus dados aqui
    }

# Carregar os dados do banco de dados
from utilidades import leitura_de_dados
try:
    st.session_state['dados']['df_vendas'] = leitura_de_dados()
    st.info("Conexão com o banco de dados bem-sucedida.")
except Exception as e:
    st.error(f"Erro ao conectar ao banco de dados: {e}")


st.sidebar.markdown('Desenvolvido por [HaroTecBusiness](https://www.harotecbusiness.com.br/)')

st.markdown('# Bem-vindo ao Analisador de Vendas')

st.divider()

# Caminho para a imagem
image_path = r"C:\Users\tito\OneDrive\Documentos\curso\pythoncurso\salesapp\projeto_completo\salesapp\Imagem\Harotec_office.jpg"

# Exibir a imagem
st.image(image_path, use_column_width=True)

st.markdown(
    '''
    Para mais informações envie para o email contato@harotecbusiness.com.br ou diretamente na nossa [HaroTecBusiness](https://www.harotecbusiness.com.br/).
    '''
            )