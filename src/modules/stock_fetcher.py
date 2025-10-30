# src/modules/stock_fetcher.py
import os
import json
import requests
import time
import datetime
from .auth import BASE_URL, FILIAL, generate_signature, get_auth_token

# --- CONFIGURAÇÃO DE CAMINHOS ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIRECTORY = os.path.join(BASE_DIR, 'data')
RAW_DATA_DIRECTORY = os.path.join(DATA_DIRECTORY, 'raw')
OUTPUT_FILE_PATH = os.path.join(RAW_DATA_DIRECTORY, 'dados_de_estoque_compilado.json')
LAST_SYNC_FILE_PATH = os.path.join(DATA_DIRECTORY, 'last_sync_estoque.txt')


def get_last_sync_date() -> str | None:
    """
    Lê a data da última sincronização do arquivo.
    Faz ajuste retrocompatível: converte formatos antigos (YYYYMMDD ou YYYYMMDD%H%M%S)
    para o novo formato YYYY-MM-DD.
    """
    try:
        with open(LAST_SYNC_FILE_PATH, 'r', encoding='utf-8') as f:
            value = f.read().strip()
            if not value:
                return None

            # Caso 1: já esteja no formato correto (YYYY-MM-DD)
            if len(value) == 10 and value[4] == "-" and value[7] == "-":
                return value

            # Caso 2: formato antigo YYYYMMDD
            if len(value) == 8 and value.isdigit():
                dt = datetime.datetime.strptime(value, "%Y%m%d")
                return dt.strftime("%Y-%m-%d")

            # Caso 3: formato antigo com hora YYYYMMDD%H%M%S
            if len(value) == 14 and value.isdigit():
                dt = datetime.datetime.strptime(value, "%Y%m%d%H%M%S")
                return dt.strftime("%Y-%m-%d")

            print(f"⚠️ Valor inválido no arquivo de sincronização: {value}")
            return None
    except FileNotFoundError:
        print("📂 Arquivo de última sincronização não encontrado. Buscando todos os dados.")
        return None


def save_last_sync_date(sync_time: str):
    """Salva a data da sincronização atual no formato YYYY-MM-DD."""
    os.makedirs(DATA_DIRECTORY, exist_ok=True)
    with open(LAST_SYNC_FILE_PATH, 'w', encoding='utf-8') as f:
        f.write(sync_time)
    print(f"💾 Data de sincronização salva: {sync_time}")


def get_item_key(item: dict) -> str | None:
    """
    Define a chave única para identificar registros de estoque.
    Usa 'codigoProduto' ou 'codigo' (dependendo de qual existir).
    """
    return str(item.get("codigoProduto") or item.get("codigo") or "")


def fetch_and_save_stock_data():
    if not (token := get_auth_token()):
        print("❌ Falha na autenticação. A execução será interrompida.")
        return

    dados_compilados = []
    auth_headers = {"Authorization": f"Token {token}"}
    
    last_sync = get_last_sync_date()
    data_ate = datetime.datetime.now().strftime("%Y-%m-%d")  # 🔹 formato correto
    
    pagina = 1
    print("🚀 Iniciando busca de dados de estoque...")

    while True:
        endpoint = f"{BASE_URL}/v2/estoque/{pagina}"
        
        params = {}
        if last_sync:
            params['datade'] = last_sync
        params['dataate'] = data_ate
        
        timestamp = str(int(time.time()))
        signature = generate_signature('get', timestamp)
        
        headers = {
            **auth_headers,
            "CodFilial": str(FILIAL),
            "Timestamp": timestamp,
            "Signature": signature
        }
        
        print(f"DEBUG: {endpoint} -> params={params}, headers={headers}")
        
        try:
            response = requests.get(endpoint, headers=headers, params=params, timeout=45)
            response.raise_for_status()
            data = response.json()

            if not data.get("sucesso") or not data.get("dados") or data.get("tipo") == "FIM_DE_PAGINA":
                print("ℹ️ Fim da paginação ou não há mais dados para buscar.")
                break
            
            dados_compilados.extend(data.get("dados", []))
            pagina += 1
            time.sleep(0.1)

        except requests.exceptions.RequestException as e:
            print(f"❌ Erro de rede na página {pagina}: {e}")
            return
        except json.JSONDecodeError:
            print(f"❌ Erro ao decodificar a resposta JSON da página {pagina}.")
            return

    # 🔹 Mesclar com dados antigos
    if dados_compilados:
        existing_records = []
        if os.path.exists(OUTPUT_FILE_PATH):
            try:
                with open(OUTPUT_FILE_PATH, 'r', encoding='utf-8') as f:
                    existing_records = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                print("⚠️ Não foi possível ler os registros existentes. Será criado um novo arquivo.")

        print(f"🔎 Total carregado do arquivo anterior: {len(existing_records)}")
        print(f"🔎 Total recebido da API: {len(dados_compilados)}")

        all_records_dict = {}
        for item in existing_records + dados_compilados:
            key = get_item_key(item)
            if key:  # só considera se tiver uma chave válida
                all_records_dict[key] = item

        final_records = list(all_records_dict.values())

        os.makedirs(RAW_DATA_DIRECTORY, exist_ok=True)
        with open(OUTPUT_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(final_records, f, ensure_ascii=False, indent=4)

        print(f"✅ Sucesso! {len(dados_compilados)} novos registros mesclados.")
        print(f"📦 Total consolidado no arquivo: {len(final_records)}")
    else:
        print("ℹ️ Nenhum dado novo de estoque foi encontrado desde a última sincronização.")
    
    # 🔹 Sempre salva a última data no novo formato (YYYY-MM-DD)
    save_last_sync_date(data_ate)
