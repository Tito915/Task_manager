import os
import streamlit as st
from home_page import home_page
from create_task import create_task
from manage_tasks import manage_tasks
from member_registration import cadastrar_membro
from approve_tasks import aprovar_tarefas
from execute_tasks import executar_tarefas, exibir_downloads
from PIL import Image
from login import login
from utils import load_tasks

# Define o caminho para salvar a imagem do usuário
# user_image_path = "\\Servidor\\c\\sallesapp\\user"

# Caminho da imagem de fundo
# background_image_path = "\\Servidor\\c\\sallesapp\\image\\wallpaper.jpg"

def show_main_content():
    st.sidebar.title("Menu")

    # Adicionando CSS para o fundo
    """
    st.markdown(
        f'''
        <style>
        .stApp {{
            background-image: url('file://{background_image_path}');
            background-size: cover;
            background-repeat: no-repeat;
            background-position: center;
            height: 100vh;  /* Altura total da janela */
            color: white;  /* Cor do texto */
        }}
        </style>
        ''',
        unsafe_allow_html=True
    )
    """

    # Exibir imagem do usuário em tamanho reduzido
    # user_icon_path = "C:/Users/tito/OneDrive/Documentos/curso/pythoncurso/Gerenciamento_Tarefas/imagens/user_icon.png"

    # Verificar se o usuário tem uma foto personalizada
    """
    user_photo_path = f"\\Servidor\\c\\sallesapp\\user\\{st.session_state.user['nome'].replace(' ', '_')}.png"  # Nome do arquivo baseado no nome do usuário
    if os.path.exists(user_photo_path):
        user_icon = Image.open(user_photo_path)
    else:
        user_icon = Image.open(user_icon_path)
    
    st.sidebar.image(user_icon, use_column_width=False, width=int(user_icon.width * 0.4))
    """

    # Mostrar o nome do usuário
    first_name = st.session_state.user['nome'].split()[0]
    st.sidebar.success(f"Seja bem-vindo: {first_name}")

    # Verificar pendências para aprovação e tarefas para executar
    num_approvals = 2  # Exemplo: substituir pela lógica real
    num_tasks = 3  # Exemplo: substituir pela lógica real

    # Exibir ícones com números de pendências
    # approval_icon_path = "C:/Users/tito/OneDrive/Documentos/curso/pythoncurso/Gerenciamento_Tarefas/imagens/Aprovação.png"
    # alert_icon_path = "C:/Users/tito/OneDrive/Documentos/curso/pythoncurso/Gerenciamento_Tarefas/imagens/Alerta.png"

    col1, col2 = st.sidebar.columns([1, 1])
    with col1:
        # st.image(approval_icon_path, width=30)
        st.write("🔔")  # Emoji como substituto para o ícone
        if num_approvals > 0:
            st.markdown(f"<a href='#aprovar-tarefas' style='text-decoration:none; color:red;'>{num_approvals}</a>", unsafe_allow_html=True)

    with col2:
        # st.image(alert_icon_path, width=30)
        st.write("⚠️")  # Emoji como substituto para o ícone
        if num_tasks > 0:
            st.markdown(f"<a href='#executar-tarefas' style='text-decoration:none; color:red;'>{num_tasks}</a>", unsafe_allow_html=True)

    menu = st.sidebar.radio("Navegação", ["Home", "Tarefas", "Gerenciamento de Tarefas", "Cadastrar Membro", "Aprovar Tarefas", "Executar Tarefas", "Downloads"])

    if menu == "Home":
        home_page()
    elif menu == "Tarefas":
        create_task()
    elif menu == "Gerenciamento de Tarefas":
        manage_tasks()
    elif menu == "Cadastrar Membro":
        if st.session_state.user['funcao'] in ['Desenvolvedor', 'Presidente']:
            cadastrar_membro(st.session_state.user)
        else:
            st.error("Você não tem permissão para cadastrar membros.")
    elif menu == "Aprovar Tarefas":
        aprovar_tarefas(st.session_state.user['nome'])
    elif menu == "Executar Tarefas":
        executar_tarefas(st.session_state.user['nome'])
    elif menu == "Downloads":
        todas_tarefas = load_tasks()
        exibir_downloads(todas_tarefas, st.session_state.user['nome'])

def main():
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    if st.session_state.user is None:
        login()  # Chamando a função de login importada de login.py
    else:
        show_main_content()

if __name__ == "__main__":
    main()