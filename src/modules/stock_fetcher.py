# src/modules/stock_fetcher.py
import os
import csv
import json
import requests
import time
from .auth import BASE_URL, FILIAL, SENHA, generate_signature, get_auth_token

# Obter o diretório base do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Caminhos corrigidos
CSV_FILE_PATH = os.path.join(BASE_DIR, 'data', 'id.csv')
OUTPUT_DIRECTORY = os.path.join(BASE_DIR, 'data', 'raw')
OUTPUT_FILE_PATH = os.path.join(OUTPUT_DIRECTORY, 'dados_de_estoque_compilado.json')

def ler_ids_do_csv() -> list[str]:
    try:
        with open(CSV_FILE_PATH, 'r', encoding='utf-8') as infile:
            return [row[0].strip() for row in csv.reader(infile) if row]
    except FileNotFoundError:
        print(f"Erro: Arquivo {CSV_FILE_PATH} não encontrado")
        return []

def fetch_and_save_stock_data():
    product_ids = ler_ids_do_csv()
    if not product_ids:
        print("Nenhum ID para processar")
        return

    if not (token := get_auth_token()):
        print("Falha na autenticação")
        return

    dados_compilados = []
    auth_headers = {"Authorization": f"Token {token}", "CodFilial": str(FILIAL)}

    for product_id in product_ids:
        endpoint = f"{BASE_URL}/v2/estoque/detalhes/{product_id}"
        timestamp = str(int(time.time()))
        signature = generate_signature('get', timestamp)
        
        headers = {
            **auth_headers,
            "Timestamp": timestamp,
            "Signature": signature
        }

        try:
            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()
            if response.json().get("sucesso"):
                dados_compilados.append(response.json().get("dados"))
        except Exception as e:
            print(f"Erro no ID {product_id}: {e}")

    if dados_compilados:
        os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
        with open(OUTPUT_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(dados_compilados, f, ensure_ascii=False, indent=4)
        print(f"Dados salvos em {OUTPUT_FILE_PATH}")