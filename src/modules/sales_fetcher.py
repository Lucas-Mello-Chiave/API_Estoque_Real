# src/modules/sales_fetcher.py
import os
import json
import time
import requests
from datetime import date, timedelta, datetime # MODIFICADO: Adicionado datetime

from .auth import BASE_URL, FILIAL, SENHA, generate_signature, get_auth_token

# Obter o diretório base do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Caminhos corrigidos
RAW_DATA_DIRECTORY = os.path.join(BASE_DIR, 'data', 'raw')
RAW_OUTPUT_FILE_PATH = os.path.join(RAW_DATA_DIRECTORY, 'saidas_ultimos_366_dias.json')

# NOVO: Caminho para o arquivo de vendas limpo, que servirá como referência
CLEANED_SALES_FILE_PATH = os.path.join(BASE_DIR, 'data', 'limpa', 'vendas.json')

PAGE_SIZE = 10

def fetch_saidas_last_366_days():
    today = date.today()
    start_date = today - timedelta(days=366) # Data padrão para a primeira execução
    
    # NOVO: Lógica para determinar a data de início da busca
    initial_fetch_date = start_date.isoformat() # Guarda a data de início original
    
    if os.path.exists(CLEANED_SALES_FILE_PATH):
        try:
            with open(CLEANED_SALES_FILE_PATH, 'r', encoding='utf-8') as f:
                limpo_data = json.load(f)
                last_fetch_date_str = limpo_data.get("dataate")
                # A nova busca começa no mesmo dia da última busca para pegar registros novos no mesmo dia
                start_date = datetime.strptime(last_fetch_date_str, '%Y-%m-%d').date()
                initial_fetch_date = limpo_data.get("datade", start_date.isoformat()) # Mantém a data de início da primeira busca
                print(f"Arquivo 'vendas.json' encontrado. Buscando vendas a partir de: {start_date.isoformat()}")
        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            print(f"Aviso: Não foi possível ler a data do arquivo 'vendas.json' ({e}). Buscando últimos 366 dias.")
    else:
        print("Nenhum arquivo 'vendas.json' encontrado. Realizando busca completa dos últimos 366 dias.")

    if not (token := get_auth_token()):
        return

    newly_compiled = []
    page = 1
    while True:
        endpoint = f"{BASE_URL}/saidas/{page}"
        params = {
            "tipodata": "A",
            "datade": start_date.isoformat(),
            "dataate": today.isoformat(),
            "codfilial": FILIAL
        }
        
        timestamp = str(int(time.time()))
        headers = {
            "Authorization": f"Token {token}",
            "CodFilial": str(FILIAL),
            "Timestamp": timestamp,
            "Signature": generate_signature('get', timestamp)
        }

        try:
            print(f"Requisitando página {page} ({start_date.isoformat()} a {today.isoformat()})")
            response = requests.get(endpoint, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("sucesso"):
                print(f"API retornou erro: {data.get('mensagem', 'Sem mensagem')}")
                break

            items = data.get("dados", [])
            items = items if isinstance(items, list) else [items]
            
            if not items: # Se a API retorna uma lista vazia na primeira página
                print("Nenhum registro novo encontrado.")
                break

            count = len(items)
            newly_compiled.extend(items)
            
            print(f"Página {page}: {count} registros recebidos")
            
            if count < PAGE_SIZE:
                print("Fim da paginação (menos registros que PAGE_SIZE)")
                break
                
            page += 1
            time.sleep(0.2)
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição HTTP: {e}")
            break
        except Exception as e:
            print(f"Erro inesperado na página {page}: {e}")
            break

    # MODIFICADO: Lógica para carregar dados antigos e juntar com os novos
    
    # Carrega os registros brutos existentes, se houver
    existing_records = []
    if os.path.exists(RAW_OUTPUT_FILE_PATH):
        try:
            with open(RAW_OUTPUT_FILE_PATH, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                existing_records = existing_data.get("registros", [])
        except (json.JSONDecodeError, FileNotFoundError):
             print(f"Aviso: Não foi possível ler o arquivo de dados brutos existente. Um novo será criado.")

    # Combina os registros, evitando duplicatas
    # Usamos um dicionário com uma chave única (a data/hora da venda) para remover duplicatas
    # Isso garante que se a API retornar um registro já existente, ele será sobrescrito.
    all_records_dict = {rec['data']: rec for rec in existing_records}
    all_records_dict.update({rec['data']: rec for rec in newly_compiled})
    
    final_records = list(all_records_dict.values())
    
    os.makedirs(RAW_DATA_DIRECTORY, exist_ok=True)
    with open(RAW_OUTPUT_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump({
            "datade": initial_fetch_date, # A data de início mais antiga
            "dataate": today.isoformat(),
            "filial": FILIAL,
            "total_registros": len(final_records),
            "registros": final_records
        }, f, ensure_ascii=False, indent=4)
    
    print("-" * 50)
    print(f"Busca finalizada.")
    print(f"Total de registros novos coletados: {len(newly_compiled)}")
    print(f"Total de registros consolidados no arquivo bruto: {len(final_records)}")
    print(f"Dados brutos salvos em {RAW_OUTPUT_FILE_PATH}")