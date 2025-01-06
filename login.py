import streamlit as st
import streamlit.components.v1 as components
import firebase_admin
from firebase_admin import credentials
import pyrebase
import json

# Carregar as credenciais do Firebase a partir dos segredos do Streamlit
firebase_credentials = json.loads(st.secrets["FIREBASE_CREDENTIALS"])

# Inicializar o Firebase (execute apenas uma vez)
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_credentials)
    firebase_admin.initialize_app(cred)

# Configuração do Firebase para o Auth UI
firebase_config = {
    "apiKey": firebase_credentials["apiKey"],
    "authDomain": firebase_credentials["authDomain"],
    "projectId": firebase_credentials["projectId"],
    "storageBucket": firebase_credentials["storageBucket"],
    "messagingSenderId": firebase_credentials["messagingSenderId"],
    "appId": firebase_credentials["appId"],
}

# Inicializar o Pyrebase
firebase = pyrebase.initialize_app(firebase_config)
auth_firebase = firebase.auth()

def login_with_firebase_ui():
    # HTML para carregar o Firebase Auth UI
    firebase_ui_html = f"""
    <script src="https://www.gstatic.com/firebasejs/8.10.0/firebase-app.js"></script>
    <script src="https://www.gstatic.com/firebasejs/8.10.0/firebase-auth.js"></script>
    <script src="https://www.gstatic.com/firebasejs/ui/6.0.1/firebase-ui-auth.js"></script>
    <link type="text/css" rel="stylesheet" href="https://www.gstatic.com/firebasejs/ui/6.0.1/firebase-ui-auth.css" />

    <div id="firebaseui-auth-container"></div>

    <script>
      var firebaseConfig = {json.dumps(firebase_config)};
      if (!firebase.apps.length) {{
        firebase.initializeApp(firebaseConfig);
      }}

      var ui = new firebaseui.auth.AuthUI(firebase.auth());
      ui.start('#firebaseui-auth-container', {{
        signInOptions: [
          firebase.auth.EmailAuthProvider.PROVIDER_ID,
          firebase.auth.GoogleAuthProvider.PROVIDER_ID,
          firebase.auth.FacebookAuthProvider.PROVIDER_ID,
        ],
        signInSuccessUrl: '/',  // Redirecionar após o login
      }});
    </script>
    """

    # Exibir o componente HTML no Streamlit
    components.html(firebase_ui_html, height=500)

def check_auth_state():
    # Verificar o estado de autenticação
    user = auth_firebase.current_user
    if user:
        st.session_state.user = {
            'email': user.email,
            'nome_completo': user.display_name or "Usuário",
            'primeiro_nome': user.display_name.split()[0] if user.display_name else "Usuário",
            'funcao': "Usuário"
        }
        st.success(f"Bem-vindo, {st.session_state.user['primeiro_nome']}!")
    else:
        st.session_state.user = None

def main():
    st.title("Login com Firebase Auth UI")

    if 'user' not in st.session_state:
        st.session_state.user = None

    if st.session_state.user:
        st.write(f"Olá, {st.session_state.user['primeiro_nome']}!")
        st.button("Sair", on_click=lambda: st.session_state.clear())
    else:
        login_with_firebase_ui()
        check_auth_state()

if __name__ == "__main__":
    main()