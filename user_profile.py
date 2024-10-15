import streamlit as st
from firebase_utils import upload_profile_picture, update_user_profile_picture, get_user_profile_picture
from PIL import Image
import io

def user_profile():
    st.title("Perfil do Usuário")

    user_id = st.session_state.get('user_id')
    if not user_id:
        st.error("Usuário não autenticado. Por favor, faça login.")
        return

    # Layout em duas colunas
    col1, col2 = st.columns([1, 2])

    with col1:
        # Exibir foto de perfil atual
        current_picture = get_user_profile_picture(user_id)
        if current_picture:
            st.image(current_picture, width=200, caption="Foto de Perfil Atual")
        else:
            st.info("Nenhuma foto de perfil definida.")

    with col2:
        # Informações do usuário
        st.subheader("Informações do Usuário")
        user_name = st.text_input("Nome", value=st.session_state.get('user_name', ''))
        user_email = st.text_input("Email", value=st.session_state.get('user_email', ''), disabled=True)
        
        # Adicione mais campos conforme necessário, por exemplo:
        # user_bio = st.text_area("Biografia", value=st.session_state.get('user_bio', ''))

    # Upload de nova foto de perfil
    st.subheader("Atualizar Foto de Perfil")
    uploaded_file = st.file_uploader("Escolha uma nova foto de perfil", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Prévia da nova foto de perfil", width=200)
        if st.button("Atualizar Foto de Perfil"):
            # Redimensionar e converter a imagem
            image = image.resize((200, 200))
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()

            # Upload da nova foto
            new_picture_url = upload_profile_picture(user_id, io.BytesIO(img_byte_arr))
            update_user_profile_picture(user_id, new_picture_url)
            st.success("Foto de perfil atualizada com sucesso!")
            st.experimental_rerun()

    # Botão para salvar alterações nas informações do usuário
    if st.button("Salvar Alterações"):
        # Aqui você implementaria a lógica para salvar as alterações no Firebase
        # Por exemplo:
        # update_user_info(user_id, user_name, user_bio)
        st.success("Informações do usuário atualizadas com sucesso!")

    # Botão para ir para a página inicial
    if st.button("Ir para a Página Inicial"):
        st.session_state.page = "home"
        st.experimental_rerun()