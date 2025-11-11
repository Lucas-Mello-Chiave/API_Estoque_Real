# src/modules/report_generator.py
import json
import csv
import os
from datetime import datetime, date, timedelta

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
        
        # Definir a data de corte para os últimos 6 meses
        data_hoje = date.today()
        data_limite = data_hoje - timedelta(days=6 * 30)
        print(f"Calculando média de vendas a partir de: {data_limite.strftime('%Y-%m-%d')}")

        # NOVO: Rastrear quais IDs realmente têm dados
        ids_com_dados = set()

        # Inicializar estruturas
        soma_6_meses = {}
        vendas_2025 = {}
        estoques = {}
        
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
                        # Marcar que este ID tem dados
                        ids_com_dados.add(cod)
                        
                        # Inicializar se necessário
                        if cod not in soma_6_meses:
                            soma_6_meses[cod] = 0.0
                        if cod not in vendas_2025:
                            vendas_2025[cod] = 0.0
                        
                        # Adicionar vendas dentro do período de 6 meses
                        if data_venda >= data_limite:
                            soma_6_meses[cod] += produto['quantidade']
                        
                        # Vendas de 2025
                        if data_venda.year == 2025:
                            vendas_2025[cod] += produto['quantidade']
        
        # Calcular médias dividindo por 6
        medias = {id: soma_6_meses.get(id, 0) / 6 for id in ids_com_dados}
        
        # Processar estoques
        with open(stock_path, 'r', encoding='utf-8') as f:
            dados_estoque = json.load(f)
            for item in dados_estoque:
                cod = item.get('codigo') or item.get('codigoProduto', '')
                if cod in ids:
                    # Marcar que este ID tem dados
                    ids_com_dados.add(cod)
                    
                    estoques[cod] = sum(
                        filial['estoqueAtual'] 
                        for filial in item.get('estoqueFiliais', [])
                    )
        
        # MODIFICADO: Gerar CSV apenas com IDs que têm dados
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['id', 'media', 'vendas_2025', 'estoque', 'vendas_6_meses'])
            
            for id in sorted(ids_com_dados):  # Apenas IDs com dados
                writer.writerow([
                    id,
                    round(medias.get(id, 0), 5),
                    vendas_2025.get(id, 0),
                    estoques.get(id, 0),
                    soma_6_meses.get(id, 0)
                ])
        
        print(f"Relatório gerado em: {output_path}")
        print(f"Total de IDs processados: {len(ids_com_dados)} de {len(ids)} disponíveis")
        return output_path
    
    except Exception as e:
        print(f"Erro ao gerar relatório: {e}")
        return None