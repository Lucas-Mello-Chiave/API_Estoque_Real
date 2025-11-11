import pandas as pd
import os
from datetime import date
from openpyxl.styles import numbers

def update_excel_from_csv():
    """
    Lê os dados do resultado.csv e os insere na aba 'info_tempo_real'
    de uma planilha Excel, substituindo a aba se ela já existir.
    Adiciona a data de execução na célula G1.
    Também inclui a coluna 'Unidade' vinda de unidade.csv.
    Formata as colunas numéricas com casas decimais apropriadas.
    NOVO: Filtra registros onde todas as colunas numéricas são zero.
    """
    # Define os caminhos baseados na estrutura do projeto
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_path = os.path.join(BASE_DIR, 'data', 'resultados', 'resultado.csv')
    unidade_path = os.path.join(BASE_DIR, 'data', 'unidade.csv')
    excel_path = os.path.join(BASE_DIR, 'data', 'resultados', 'ESTOQUE PRODUTOS REVISTAS.xlsx')
    sheet_name = 'info_tempo_real'

    print(f"Iniciando atualização da planilha: {os.path.basename(excel_path)}")

    try:
        # Verifica se o arquivo CSV de origem existe
        if not os.path.exists(csv_path):
            print(f"Erro: Arquivo de origem '{csv_path}' não encontrado.")
            return

        # Lê o arquivo resultado.csv com codificação compatível com Excel/Windows
        print(f"Lendo dados de: {os.path.basename(csv_path)}")
        df = pd.read_csv(csv_path, delimiter=';', encoding='latin1')

        # NOVO: Filtrar registros onde todas as colunas numéricas são zero
        print(f"Total de registros antes da filtragem: {len(df)}")
        
        # Identificar colunas numéricas (exceto 'id')
        numeric_cols = ['media', 'vendas_2025', 'estoque', 'vendas_6_meses']
        
        # Criar máscara: manter apenas linhas onde pelo menos uma coluna numérica é diferente de zero
        mask = (df[numeric_cols] != 0).any(axis=1)
        df = df[mask]
        
        print(f"Total de registros após filtrar zeros: {len(df)}")

        # Se existir o arquivo unidade.csv, faz o merge para adicionar a coluna Unidade
        if os.path.exists(unidade_path):
            print(f"Lendo unidades de: {os.path.basename(unidade_path)}")
            df_unidade = pd.read_csv(unidade_path, delimiter=';', encoding='latin1')

            # Converter ambas as colunas 'id' para inteiro antes do merge
            if 'id' in df_unidade.columns and 'id' in df.columns:
                # Remover linhas com id vazio/NaN antes da conversão
                df = df.dropna(subset=['id'])
                df_unidade = df_unidade.dropna(subset=['id'])
                
                # Filtrar apenas IDs numéricos no df_unidade (remove 'COD.1860' e similares)
                df_unidade['id'] = pd.to_numeric(df_unidade['id'], errors='coerce')
                df_unidade = df_unidade.dropna(subset=['id'])
                
                # Converter para int e MANTER como número (não converter para string)
                df['id'] = df['id'].astype(float).astype(int)
                df_unidade['id'] = df_unidade['id'].astype(int)

                df = df.merge(df_unidade[['id', 'Unidade']], on='id', how='left')
                print("Coluna 'Unidade' adicionada com sucesso.")
                
                # DEBUG: mostrar quantos IDs fizeram match
                print(f"Total de registros: {len(df)}")
                print(f"Registros com Unidade preenchida: {df['Unidade'].notna().sum()}")
                print(f"Primeiras linhas do DataFrame:\n{df.head()}")
            else:
                print("Aviso: Um dos arquivos não contém a coluna 'id'. Nenhum merge realizado.")
        else:
            print("Aviso: Arquivo 'unidade.csv' não encontrado. Continuando sem a coluna Unidade.")

        # Ajuste de casas decimais no DataFrame antes de escrever
        if 'media' in df.columns:
            df['media'] = df['media'].astype(float).round(5)

        # Determina o modo de escrita. Se o arquivo Excel não existe, usamos 'w' (write).
        # Se ele já existe, usamos 'a' (append/modify) para não apagar outras abas.
        mode = 'a' if os.path.exists(excel_path) else 'w'
        
        # Utiliza o ExcelWriter para ter controle sobre a escrita na planilha
        with pd.ExcelWriter(
            excel_path, 
            engine='openpyxl', 
            mode=mode,
            if_sheet_exists='replace'  # Substitui a aba se existir
        ) as writer:
            print(f"Escrevendo dados na aba '{sheet_name}'...")
            # Converte o DataFrame para uma planilha Excel, sem o índice do pandas
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Acessar a planilha (worksheet) que acabamos de criar/substituir
            workbook = writer.book
            worksheet = workbook[sheet_name]
            
            # Escrever a data na célula G1
            execution_date = date.today().strftime('%d/%m/%Y')
            worksheet['G1'] = execution_date
            print(f"Adicionando data de execução '{execution_date}' na célula G1.")
            
            # FORMATAÇÃO: definir número de casas decimais no Excel
            # Mapeie nomes de colunas para formatos
            number_format_map = {
                'id': '0',                   # número inteiro (NOVO)
                'media': '0.00000',          # 5 casas decimais
                'vendas_6_meses': '0',       # número inteiro
                'vendas_2025': '0',          # número inteiro
                'estoque': '0'               # número inteiro
            }

            # Descobrir o índice da coluna por nome e aplicar o formato
            header_row = 1
            headers = [cell.value for cell in worksheet[header_row]]
            for col_idx, col_name in enumerate(headers, start=1):
                fmt = number_format_map.get(col_name)
                if fmt:
                    for row in range(header_row + 1, worksheet.max_row + 1):
                        cell = worksheet.cell(row=row, column=col_idx)
                        cell.number_format = fmt
            
            print("Formatação de casas decimais aplicada com sucesso.")
        
        print("✅ Planilha atualizada com sucesso!")
        return excel_path

    except Exception as e:
        print(f"❌ Ocorreu um erro ao atualizar a planilha: {e}")
        return None