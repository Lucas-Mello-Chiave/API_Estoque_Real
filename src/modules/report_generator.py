# src/modules/report_generator.py
import json
import csv
import os
from datetime import datetime, date, timedelta # MODIFICADO: Importa 'date' e 'timedelta'

def generate_report():
    """Gera relatório CSV com dados consolidados"""
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Caminhos de entrada
    ids_path = os.path.join(BASE_DIR, 'data', 'id.csv')
    sales_path = os.path.join(BASE_DIR, 'data', 'limpa', 'vendas.json')
    stock_path = os.path.join(BASE_DIR, 'data', 'raw', 'dados_de_estoque_compilado.json')
    
    # Caminho de saída
    output_path = os.path.join(BASE_DIR, 'data', 'resultados', 'resultado.csv')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        # Ler IDs
        with open(ids_path, 'r', encoding='utf-8') as f:
            ids = [line.strip() for line in f.readlines()]
        
        # --- INÍCIO DAS MODIFICAÇÕES ---

        # 1. NOVO: Definir a data de corte para os últimos 7 meses
        # Usamos uma aproximação de 30 dias por mês.
        data_hoje = date.today()
        data_limite = data_hoje - timedelta(days=7 * 30)
        print(f"Calculando média de vendas a partir de: {data_limite.strftime('%Y-%m-%d')}")

        # Inicializar estruturas
        soma_7_meses = {id: 0.0 for id in ids} # MODIFICADO: Renomeado de 'soma_12_meses'
        vendas_2025 = {id: 0.0 for id in ids}
        estoques = {id: 0.0 for id in ids}
        
        # Processar vendas
        with open(sales_path, 'r', encoding='utf-8') as f:
            dados_vendas = json.load(f)
            
            for registro in dados_vendas['registros']:
                if not registro.get('data'):
                    continue
                    
                try:
                    data_venda = datetime.strptime(registro['data'].split('T')[0], '%Y-%m-%d').date()
                except (ValueError, AttributeError):
                    continue
                
                for produto in registro['produtos']:
                    cod = produto['codigo']
                    if cod in ids:
                        # 2. NOVO: Adiciona um filtro para considerar apenas vendas dentro do período de 7 meses
                        if data_venda >= data_limite:
                            soma_7_meses[cod] += produto['quantidade'] # MODIFICADO: Usa a nova variável
                        
                        # A lógica de vendas de 2025 permanece a mesma
                        if data_venda.year == 2025:
                            vendas_2025[cod] += produto['quantidade']
        
        # 3. MODIFICADO: Calcular médias dividindo por 7
        medias = {id: soma_7_meses[id] / 7 for id in ids}
        
        # --- FIM DAS MODIFICAÇÕES ---
        
        # Processar estoques (esta seção permanece inalterada)
        with open(stock_path, 'r', encoding='utf-8') as f:
            dados_estoque = json.load(f)
            for item in dados_estoque:
                cod = item.get('codigo') or item.get('codigoProduto', '')
                if cod in ids:
                    estoques[cod] = sum(
                        filial['estoqueAtual'] 
                        for filial in item.get('estoqueFiliais', [])
                    )
        
        # Gerar CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['id', 'media', 'vendas_2025', 'estoque'])
            
            for id in ids:
                writer.writerow([
                    id,
                    round(medias.get(id, 0), 2),
                    vendas_2025.get(id, 0),
                    estoques.get(id, 0)
                ])
        
        print(f"Relatório gerado em: {output_path}")
        return output_path
    
    except Exception as e:
        print(f"Erro ao gerar relatório: {e}")
        return None