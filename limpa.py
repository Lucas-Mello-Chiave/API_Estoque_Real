import pandas as pd

# Carregar o arquivo CSV
df = pd.read_csv('dados_filtrado.csv', delimiter=';')

# Converter a coluna 'Id' para um tipo numérico e depois para inteiro
df['Id'] = pd.to_numeric(df['Id'], errors='coerce').astype(int)

# Salvar o arquivo modificado com a mesma formatação
df.to_csv('dados_filtrado.csv', sep=';', index=False)