import streamlit as st
import json
from firebase_admin import storage
import io

def carregar_taxas():
    try:
        bucket = storage.bucket()
        blob = bucket.blob('SallesApp/taxaatualizacao.json')
        
        # Download do arquivo para a memória
        data = blob.download_as_string()
        
        # Decodificar o JSON
        taxas = json.loads(data)
        return taxas
    except Exception as e:
        st.error(f"Erro ao carregar taxas: {e}")
        return {'cartao': {str(i): 0.0 for i in range(1, 13)}, 'boleto': {str(i): 0.0 for i in range(1, 13)}}

def calcular_valor_final():
    try:
        valor_venda = float(st.session_state['valor_venda'])
        entrada = float(st.session_state['entrada'])
        parcelas = int(st.session_state['parcelas'])
        
        cliente_paga_taxas = st.session_state['cliente_paga']
        
        if st.session_state['pagamento'] == 'Boleto':
            taxa = float(taxas_boleto.get(str(parcelas), 0))
        elif st.session_state['pagamento'] == 'Cartão':
            taxa = float(taxas_cartao.get(str(parcelas), 0))
            taxa_antecipacao = float(st.session_state.get('taxa_antecipacao', 0.0))
            if cliente_paga_taxas:
                taxa += taxa_antecipacao * parcelas
        else:
            st.error("Selecione uma forma de pagamento.")
            return
        
        valor_restante = valor_venda - entrada
        
        if cliente_paga_taxas:
            valor_final = valor_restante + (valor_restante * (taxa / 100))
            valor_recebido = valor_final
        else:
            valor_final = valor_restante
            valor_recebido = valor_restante - (valor_restante * (taxa / 100))
        
        st.session_state['valor_final'] = valor_final
        st.session_state['valor_recebido'] = valor_recebido
        
        valor_parcela = valor_final / parcelas
        st.session_state['parcelas_detalhes'] = [
            f"Parcela {i+1}: R$ {valor_parcela:.2f}" for i in range(parcelas)
        ]
        
    except ValueError:
        st.error("Por favor, insira valores numéricos válidos.")

def main():
    st.title("Cálculo de Venda a Prazo")

    # Carregar taxas do Firebase Storage
    global taxas_cartao, taxas_boleto
    taxas = carregar_taxas()
    taxas_cartao = taxas['cartao']
    taxas_boleto = taxas['boleto']

    # Inicializar variáveis de sessão
    if 'valor_venda' not in st.session_state:
        st.session_state['valor_venda'] = ''
    if 'entrada' not in st.session_state:
        st.session_state['entrada'] = ''
    if 'parcelas' not in st.session_state:
        st.session_state['parcelas'] = 1
    if 'pagamento' not in st.session_state:
        st.session_state['pagamento'] = 'Boleto'
    if 'cliente_paga' not in st.session_state:
        st.session_state['cliente_paga'] = False
    if 'taxa_antecipacao' not in st.session_state:
        st.session_state['taxa_antecipacao'] = 0.0

    # Interface do usuário
    col1, col2 = st.columns(2)

    with col1:
        st.text_input("Valor total da venda (R$):", key='valor_venda')
        st.text_input("Valor da entrada (R$):", key='entrada')
        st.selectbox("Número de parcelas:", options=list(range(1, 13)), key='parcelas')

    with col2:
        st.radio("Forma de pagamento:", options=['Boleto', 'Cartão'], key='pagamento')
        st.checkbox("Cliente paga as taxas", key='cliente_paga')
        if st.session_state['pagamento'] == 'Cartão':
            st.text_input("Taxa de Antecipação (%):", key='taxa_antecipacao')

    if st.button("Calcular"):
        calcular_valor_final()

    # Exibir resultados
    if 'valor_final' in st.session_state:
        st.markdown("### Resultados")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Valor final a ser pago", f"R$ {st.session_state['valor_final']:.2f}")
        with col2:
            st.metric("Valor a ser recebido", f"R$ {st.session_state['valor_recebido']:.2f}")

        st.markdown("### Detalhes das Parcelas")
        if 'parcelas_detalhes' in st.session_state:
            for detalhe in st.session_state['parcelas_detalhes']:
                st.write(detalhe)

if __name__ == "__main__":
    main()