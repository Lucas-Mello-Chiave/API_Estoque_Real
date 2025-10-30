# src/modules/data_cleaner.py
import json
import os

def clean_sales_data():
    """
    Processa dados de vendas brutos:
    1. Filtra registros mantendo apenas operações de VND
    2. Extrai campos essenciais
    3. Salva em /data/limpa/vendas.json
    """
    # Caminhos corrigidos
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    input_path = os.path.join(BASE_DIR, 'data', 'raw', 'saidas_ultimos_366_dias.json')
    output_path = os.path.join(BASE_DIR, 'data', 'limpa', 'vendas.json')
    
    # Criar diretório se não existir
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            dados = json.load(f)
        
        # Filtrar apenas operações VND
        dados["registros"] = [r for r in dados["registros"] if r.get("tipo_Operacao") == "VND"]
        
        # Limpar campos
        dados["registros"] = [
            {
                "tipo_Operacao": r.get("tipo_Operacao"),
                "data": r.get("data"),
                "produtos": [
                    {
                        "codigo": p.get("codigo"),
                        "quantidade": p.get("quantidade")
                    }
                    for p in r.get("produtos", [])
                ]
            }
            for r in dados["registros"]
        ]
        
        # Atualizar contagem
        dados["total_registros"] = len(dados["registros"])
        
        # Salvar resultado
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
        
        print(f"Dados de vendas limpos salvos em: {output_path}")
        return output_path
    
    except Exception as e:
        print(f"Erro ao processar dados de vendas: {e}")
        return None