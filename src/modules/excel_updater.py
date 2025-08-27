import pandas as pd
import os
from datetime import date # <--- 1. Importar o módulo de data

def update_excel_from_csv():
    """
    Lê os dados do resultado.csv e os insere na aba 'info_tempo_real'
    de uma planilha Excel, substituindo a aba se ela já existir.
    Adiciona a data de execução na célula D1.
    """
    # Define os caminhos baseados na estrutura do projeto
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_path = os.path.join(BASE_DIR, 'data', 'resultados', 'resultado.csv')
    excel_path = os.path.join(BASE_DIR, 'data', 'resultados', 'ESTOQUE PRODUTOS REVISTAS.xlsx')
    sheet_name = 'info_tempo_real'

    print(f"Iniciando atualização da planilha: {os.path.basename(excel_path)}")

    try:
        # Verifica se o arquivo CSV de origem existe
        if not os.path.exists(csv_path):
            print(f"Erro: Arquivo de origem '{csv_path}' não encontrado.")
            return

        # Lê o arquivo CSV usando pandas. É crucial especificar o delimitador ';'.
        print(f"Lendo dados de: {os.path.basename(csv_path)}")
        df = pd.read_csv(csv_path, delimiter=';')

        # Determina o modo de escrita. Se o arquivo Excel não existe, usamos 'w' (write).
        # Se ele já existe, usamos 'a' (append/modify) para não apagar outras abas.
        mode = 'a' if os.path.exists(excel_path) else 'w'
        
        # Utiliza o ExcelWriter para ter controle sobre a escrita na planilha
        with pd.ExcelWriter(
            excel_path, 
            engine='openpyxl', 
            mode=mode,
            if_sheet_exists='replace' # A mágica acontece aqui: substitui a aba se existir
        ) as writer:
            print(f"Escrevendo dados na aba '{sheet_name}'...")
            # Converte o DataFrame para uma planilha Excel, sem o índice do pandas
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # --- INÍCIO DA MODIFICAÇÃO ---
            # 2. Obter a data atual no formato desejado
            execution_date = date.today().strftime('%d/%m/%Y')

            # 3. Acessar a planilha (worksheet) que acabamos de criar/substituir
            workbook = writer.book
            worksheet = workbook[sheet_name]
            
            # 4. Escrever a data na célula D1
            worksheet['E1'] = execution_date
            print(f"Adicionando data de execução '{execution_date}' na célula D1.")
            # --- FIM DA MODIFICAÇÃO ---
        
        print("Planilha atualizada com sucesso!")
        return excel_path

    except Exception as e:
        print(f"Ocorreu um erro ao atualizar a planilha: {e}")
        return None