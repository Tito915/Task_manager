import streamlit as st
import json
from firebase_admin import storage
import io
import pandas as pd


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
    
def salvar_taxas(taxas):
    try:
        bucket = storage.bucket()
        blob = bucket.blob('SallesApp/taxaatualizacao.json')
        
        # Converter taxas para JSON e salvar
        json_data = json.dumps(taxas)
        blob.upload_from_string(json_data, content_type='application/json')
        
        st.success("Taxas atualizadas com sucesso!")
    except Exception as e:
        st.error(f"Erro ao salvar taxas: {e}")
        
def calcular_valor_final():
    try:
        valor_venda = float(st.session_state['valor_venda'] or 0)
        entrada = float(st.session_state['entrada'] or 0)
        parcelas = int(st.session_state['parcelas'])
        
        cliente_paga_taxas = st.session_state['cliente_paga']
        
        if st.session_state['pagamento'] == 'Boleto':
            taxa = float(taxas_boleto.get(str(parcelas), 0))
        elif st.session_state['pagamento'] == 'Cartão':
            taxa = float(taxas_cartao.get(str(parcelas), 0))
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
        
        valor_parcela = valor_final / parcelas if parcelas > 0 else 0
        st.session_state['parcelas_detalhes'] = [
            f"Parcela {i+1}: R$ {valor_parcela:.2f}" for i in range(parcelas)
        ]
        
    except ValueError as e:
        st.error(f"Erro de valor: {e}. Por favor, insira valores numéricos válidos.")
    except Exception as e:
        st.error(f"Erro inesperado: {e}")

def exibir_taxas(taxas):
    st.subheader("Taxas Cadastradas")
    
    df_cartao = pd.DataFrame(list(taxas['cartao'].items()), columns=['Parcelas', 'Taxa (%)'])
    df_cartao['Parcelas'] = df_cartao['Parcelas'].astype(int)
    df_cartao = df_cartao.sort_values('Parcelas')
    
    df_boleto = pd.DataFrame(list(taxas['boleto'].items()), columns=['Parcelas', 'Taxa (%)'])
    df_boleto['Parcelas'] = df_boleto['Parcelas'].astype(int)
    df_boleto = df_boleto.sort_values('Parcelas')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Taxas de Cartão")
        st.dataframe(df_cartao)
    
    with col2:
        st.write("Taxas de Boleto")
        st.dataframe(df_boleto)

def main():
    st.title("Cálculo de Venda a Prazo")

    # Carregar taxas do Firebase Storage
    if 'taxas' not in st.session_state:
        st.session_state['taxas'] = carregar_taxas()

    # Botão para atualizar taxas
    if st.button("Atualizar Taxas"):
        st.session_state['taxas'] = carregar_taxas()
        st.success("Taxas atualizadas com sucesso!")

    global taxas_cartao, taxas_boleto
    taxas_cartao = st.session_state['taxas']['cartao']
    taxas_boleto = st.session_state['taxas']['boleto']

    # Inicializar variáveis de sessão
    if 'valor_venda' not in st.session_state:
        st.session_state['valor_venda'] = ''
    if 'entrada' not in st.session_state:
        st.session_state['entrada'] = ''
    if 'parcelas' not in st.session_state:
        st.session_state['parcelas'] = 1
    if 'pagamento' not in st.session_state:
        st.session_state['pagamento'] = 'Cartão'
    if 'cliente_paga' not in st.session_state:
        st.session_state['cliente_paga'] = True

    # Criar abas
    tab1, tab2 = st.tabs(["Calculadora", "Gerenciar Taxas"])

    with tab1:
        # Interface do usuário da calculadora
        col1, col2 = st.columns(2)

        with col1:
            st.text_input("Valor total da venda (R$):", key='valor_venda')
            st.text_input("Valor da entrada (R$):", key='entrada')
            st.selectbox("Número de parcelas:", options=list(range(1, 13)), key='parcelas')

        with col2:
            st.radio("Forma de pagamento:", options=['Cartão', 'Boleto'], key='pagamento')
            st.checkbox("Cliente paga as taxas", key='cliente_paga', value=True)

        if st.button("Calcular"):
            calcular_valor_final()

        # Exibir resultados
        if 'valor_final' in st.session_state and 'valor_recebido' in st.session_state:
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

    with tab2:
        if 'user' in st.session_state and st.session_state.user.get('funcao') == 'Desenvolvedor':
            st.markdown("### Gerenciamento de Taxas")
            
            # Exibir taxas atuais
            exibir_taxas(st.session_state['taxas'])
            
            st.markdown("---")
            st.markdown("### Cadastro de Taxas")
            
            taxa_type = st.radio("Tipo de Taxa:", options=['Cartão', 'Boleto'])
            
            col1, col2 = st.columns(2)
            with col1:
                parcela = st.selectbox("Número de parcelas:", options=list(range(1, 13)))
            with col2:
                taxa = st.number_input("Taxa (%):", min_value=0.0, max_value=100.0, step=0.01)
            
            if st.button("Atualizar Taxa"):
                if taxa_type == 'Cartão':
                    st.session_state['taxas']['cartao'][str(parcela)] = taxa
                else:
                    st.session_state['taxas']['boleto'][str(parcela)] = taxa
                salvar_taxas(st.session_state['taxas'])
                st.success(f"Taxa de {taxa}% para {parcela} parcela(s) no {taxa_type} atualizada com sucesso!")
                st.rerun()  # Recarrega a página para exibir as taxas atualizadas
        else:
            st.warning("Acesso restrito. Apenas desenvolvedores podem gerenciar as taxas.")

if __name__ == "__main__":
    main()