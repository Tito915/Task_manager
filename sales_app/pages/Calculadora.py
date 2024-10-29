import streamlit as st
import json
import os

def carregar_taxas():
    # Obtenha o caminho absoluto para o arquivo JSON
    caminho_diretorio = os.path.dirname(__file__)
    caminho_arquivo = os.path.join(caminho_diretorio, 'taxaatualizacao.json')
    
    # Inicializa taxas padrão
    taxas_padrao = {'cartao': {str(i): 0.0 for i in range(1, 13)}, 'boleto': {str(i): 0.0 for i in range(1, 13)}}
    
    if os.path.exists(caminho_arquivo):
        with open(caminho_arquivo, 'r') as file:
            try:
                data = file.read().strip()
                if data:
                    return json.loads(data)
                else:
                    st.error("Arquivo JSON vazio. Usando taxas padrão.")
            except json.JSONDecodeError:
                st.error("Erro ao decodificar o arquivo JSON. Usando taxas padrão.")
    
    return taxas_padrao

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
        
        # Simulação das parcelas
        valor_parcela = valor_final / parcelas
        st.session_state['parcelas_detalhes'] = [
            f"Parcela {i+1}: R$ {valor_parcela:.2f}" for i in range(parcelas)
        ]
        
    except ValueError:
        st.error("Por favor, insira valores numéricos válidos.")

def run_calculator():
    # Inicialização das chaves no session_state
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

    st.title("Cálculo de Venda a Prazo")

    taxas = carregar_taxas()
    global taxas_cartao, taxas_boleto
    taxas_cartao = taxas['cartao']
    taxas_boleto = taxas['boleto']

    st.text_input("Valor total da venda (R$):", key='valor_venda')
    st.text_input("Valor da entrada (R$):", key='entrada')
    st.selectbox("Número de parcelas:", options=list(range(1, 13)), key='parcelas')
    st.radio("Forma de pagamento:", options=['Boleto', 'Cartão'], key='pagamento')
    st.checkbox("Cliente paga as taxas", key='cliente_paga')

    if st.session_state['pagamento'] == 'Cartão':
        st.text_input("Taxa de Antecipação (%):", key='taxa_antecipacao')

    if st.button("Calcular"):
        calcular_valor_final()

    st.write(f"Valor final a ser pago (R$): {st.session_state.get('valor_final', '')}")
    st.write(f"Valor a ser recebido (R$): {st.session_state.get('valor_recebido', '')}")

    if 'parcelas_detalhes' in st.session_state:
        for detalhe in st.session_state['parcelas_detalhes']:
            st.write(detalhe)
            
def main(ambiente):
    # Normaliza o nome do ambiente
    ambiente_normalizado = ambiente.replace(" ", "").lower()
    
    if ambiente_normalizado == "salesapp":
        # Código específico para Sales App
        st.write("Executando no ambiente Sales App")
        run_calculator()
    else:
        st.write("Outro ambiente")
