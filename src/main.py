# src/main.py

# MODIFICADO: Adicionado o novo módulo 'excel_updater'
from modules import stock_fetcher, sales_fetcher, data_cleaner, report_generator, excel_updater

def run_pipeline():
    print("="*50)
    print("Coletando dados de estoque...")
    stock_fetcher.fetch_and_save_stock_data()
    
    print("\n" + "="*50)
    print("Coletando dados de vendas...")
    sales_fetcher.fetch_saidas_last_366_days()
    
    print("\n" + "="*50)
    print("Processando dados de vendas...")
    data_cleaner.clean_sales_data()
    
    print("\n" + "="*50)
    print("Gerando relatório final em CSV...")
    report_generator.generate_report()

    # NOVO: Adiciona a etapa de atualização da planilha Excel
    print("\n" + "="*50)
    print("Atualizando planilha Excel...")
    excel_updater.update_excel_from_csv()
    
    print("\n" + "="*50)
    print("Pipeline concluído com sucesso!")

if __name__ == "__main__":
    run_pipeline()