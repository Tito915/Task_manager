import pandas as pd
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import json
from datetime import datetime
import chardet
import math

# Inicializar o Firebase Admin SDK
cred = credentials.Certificate("C:/Users/tito/OneDrive/Documentos/curso/pythoncurso/Gerenciamento_Tarefas/firebase_credentials.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://gerenciador-de-tarefas-mbv-default-rtdb.firebaseio.com/'
})

# Função para limpar e converter strings
def clean_string(value):
    if isinstance(value, str):
        return value.strip().strip('"').strip("'")
    return value

# Função para converter uma linha do DataFrame em um dicionário
def row_to_dict(row):
    def safe_value(value):
        if pd.isna(value) or (isinstance(value, float) and math.isnan(value)):
            return None
        if isinstance(value, (int, float)):
            return value
        try:
            return float(value)
        except ValueError:
            return str(value)

    return {
        'data': row['DATA'].strftime('%Y-%m-%d') if pd.notnull(row['DATA']) else None,
        'vendedor': clean_string(row['Vendedor']),
        'razao': clean_string(row['RAZAO']),
        'qtde': safe_value(row['QTDE']),
        'valor': safe_value(row['VALOR']),
        'valor_total_liquido': safe_value(row['Valor total Liquido']),
        'gru': clean_string(row['GRU'])
    }

# Detectar a codificação do arquivo
file_path = "C:/Users/tito/OneDrive/Documentos/MBV/Madeireira/VENDAS/Power Bi/Fat_Ctrl/Faturamento_total_csv.csv"
with open(file_path, 'rb') as file:
    raw_data = file.read()
    result = chardet.detect(raw_data)
    encoding = result['encoding']

print(f"Detected encoding: {encoding}")

# Carregar o arquivo CSV com a codificação detectada
df = pd.read_csv(file_path, encoding=encoding, low_memory=False)

# Remover linhas completamente vazias
df = df.dropna(how='all')

# Limpar espaços e aspas das colunas de string
string_columns = ['Vendedor', 'CLIENTE', 'NOME', 'RAZAO', 'TELEFONE', 'CELULAR', 'CNPJ_CPF', 'ENDERECO', 'BAIRRO', 'CIDADE', 'UF', 'EMAIL', 'CONTATO', 'GRUITEM', 'PRODUTO', 'DATA', 'NOTA', 'VEND', 'NATURE', 'GRU']
for col in string_columns:
    df[col] = df[col].apply(clean_string)

print("Colunas no DataFrame:")
print(df.columns)
print("\nPrimeiras linhas do DataFrame:")
print(df.head())

# Converter as colunas para os tipos corretos
df['DATA'] = pd.to_datetime(df['DATA'], format='%Y-%m-%d', errors='coerce')
df['QTDE'] = pd.to_numeric(df['QTDE'], errors='coerce')
df['VALOR'] = pd.to_numeric(df['VALOR'], errors='coerce')
df['Valor total Liquido'] = pd.to_numeric(df['Valor total Liquido'], errors='coerce')

# Criar um dicionário com os dados
data_dict = {}
for index, row in df.iterrows():
    if pd.isnull(row['DATA']):
        continue  # Pular linhas com data inválida
    
    year = row['DATA'].year
    month = row['DATA'].month
    day = row['DATA'].day
    
    if year not in data_dict:
        data_dict[year] = {}
    if month not in data_dict[year]:
        data_dict[year][month] = {}
    if day not in data_dict[year][month]:
        data_dict[year][month][day] = []
    
    data_dict[year][month][day].append(row_to_dict(row))

# Função para remover valores NaN recursivamente
def remove_nan(obj):
    if isinstance(obj, dict):
        return {k: remove_nan(v) for k, v in obj.items() if v is not None and not (isinstance(v, float) and math.isnan(v))}
    elif isinstance(obj, list):
        return [remove_nan(item) for item in obj if item is not None and not (isinstance(item, float) and math.isnan(item))]
    elif isinstance(obj, float) and math.isnan(obj):
        return None
    else:
        return obj

# Limpar o dicionário de dados
clean_data_dict = remove_nan(data_dict)

# Enviar os dados para o Firebase Realtime Database
ref = db.reference('faturamento')
ref.set(clean_data_dict)

print("Dados migrados com sucesso para o Firebase Realtime Database!")