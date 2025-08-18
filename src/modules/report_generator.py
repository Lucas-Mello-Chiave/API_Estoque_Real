# src/modules/report_generator.py
import json
import csv
import os
from datetime import datetime

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
        
        # Inicializar estruturas
        soma_12_meses = {id: 0.0 for id in ids}
        vendas_2025 = {id: 0.0 for id in ids}
        estoques = {id: 0.0 for id in ids}
        
        # Processar vendas
        with open(sales_path, 'r', encoding='utf-8') as f:
            dados_vendas = json.load(f)
            
            for registro in dados_vendas['registros']:
                if not registro.get('data'):
                    continue
                    
                try:
                    data_venda = datetime.strptime(registro['data'].split('T')[0], '%Y-%m-%d')
                except (ValueError, AttributeError):
                    continue
                
                for produto in registro['produtos']:
                    cod = produto['codigo']
                    if cod in ids:
                        soma_12_meses[cod] += produto['quantidade']
                        if data_venda.year == 2025:
                            vendas_2025[cod] += produto['quantidade']
        
        # Calcular médias
        medias = {id: soma_12_meses[id] / 12 for id in ids}
        
        # Processar estoques
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