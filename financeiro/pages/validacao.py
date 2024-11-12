import pandas as pd
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