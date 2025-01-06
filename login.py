import streamlit as st
import streamlit.components.v1 as components
import firebase_admin
from firebase_admin import credentials, auth
import json
import requests

# Carregar as credenciais do Firebase a partir dos segredos do Streamlit
firebase_credentials = json.loads(st.secrets["FIREBASE_CREDENTIALS"])

# Inicializar o Firebase Admin SDK (execute apenas uma vez)
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
        callbacks: {{
          signInSuccessWithAuthResult: function(authResult, redirectUrl) {{
            // Enviar o token ID para o backend
            var idToken = authResult.user.getIdToken().then(function(idToken) {{
              fetch('/verify_token', {{
                method: 'POST',
                headers: {{
                  'Content-Type': 'application/json',
                }},
                body: JSON.stringify({{ idToken: idToken }})
              }}).then(function() {{
                window.location.reload();
              }});
            }});
            return false;
          }}
        }}
      }});
    </script>
    """

    # Exibir o componente HTML no Streamlit
    components.html(firebase_ui_html, height=500)

def verify_token():
    if 'idToken' in st.session_state:
        try:
            # Verify the ID token
            decoded_token = auth.verify_id_token(st.session_state.idToken)
            uid = decoded_token['uid']
            user = auth.get_user(uid)
            st.session_state.user = {
                'email': user.email,
                'nome_completo': user.display_name or "Usuário",
                'primeiro_nome': user.display_name.split()[0] if user.display_name else "Usuário",
                'funcao': "Usuário"
            }
            return True
        except Exception as e:
            st.error(f"Erro ao verificar token: {e}")
            st.session_state.user = None
            return False
    return False

def main():
    st.title("Login com Firebase Auth UI")

    if 'user' not in st.session_state:
        st.session_state.user = None

    # Endpoint para verificar o token
    if st.experimental_get_query_params().get("verify_token"):
        token = st.experimental_get_query_params()["idToken"][0]
        st.session_state.idToken = token
        verify_token()
        st.experimental_set_query_params()

    if st.session_state.user:
        st.write(f"Olá, {st.session_state.user['primeiro_nome']}!")
        if st.button("Sair"):
            st.session_state.clear()
            st.experimental_rerun()
    else:
        login_with_firebase_ui()

if __name__ == "__main__":
    main()