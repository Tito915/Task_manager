import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

class ValidacaoCobranca:
    @staticmethod
    def verificar_duplicidade_cobranca(df: pd.DataFrame) -> pd.DataFrame:
        """
        Verifica se há duplicidade de cobrança para o mesmo cliente
        
        Args:
            df (pd.DataFrame): DataFrame de cobrança
        
        Returns:
            pd.DataFrame: Clientes com cobranças duplicadas
        """
        duplicados = df[df.duplicated(subset=['CPF/CNPJ'], keep=False)]
        return duplicados

    @staticmethod
    def verificar_status_divida(df: pd.DataFrame) -> pd.DataFrame:
        """
        Identifica clientes realmente devedores
        
        Args:
            df (pd.DataFrame): DataFrame de cobrança
        
        Returns:
            pd.DataFrame: Clientes com dívidas ativas
        """
        hoje = datetime.now()
        devedores = df[
            (df['Status Pagamento'] != 'Pago') & 
            (df['Data Vencimento'] < hoje)
        ]
        return devedores

def main():
    st.title("Validação de Cobrança")

    # Upload do arquivo CSV
    uploaded_file = st.file_uploader("Escolha um arquivo CSV", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        
        st.subheader("Dados Carregados")
        st.dataframe(df)

        validacao = ValidacaoCobranca()

        if st.button("Verificar Duplicidades"):
            duplicados = validacao.verificar_duplicidade_cobranca(df)
            if not duplicados.empty:
                st.subheader("Cobranças Duplicadas")
                st.dataframe(duplicados)
            else:
                st.success("Não foram encontradas cobranças duplicadas.")

        if st.button("Verificar Devedores"):
            devedores = validacao.verificar_status_divida(df)
            if not devedores.empty:
                st.subheader("Clientes Devedores")
                st.dataframe(devedores)
            else:
                st.success("Não foram encontrados clientes devedores.")

    else:
        st.info("Por favor, faça o upload de um arquivo CSV para iniciar a validação.")

if __name__ == "__main__":
    main()