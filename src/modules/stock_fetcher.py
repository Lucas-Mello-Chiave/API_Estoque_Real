# src/modules/stock_fetcher.py
import os
import json
import requests
import time
import datetime
from .auth import BASE_URL, FILIAL, generate_signature, get_auth_token

# --- CONFIGURAÇÃO DE CAMINHOS ---
# Obtém o diretório base do projeto para garantir que os caminhos funcionem em qualquer máquina
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Define os caminhos para os diretórios e arquivos de dados
DATA_DIRECTORY = os.path.join(BASE_DIR, 'data')
RAW_DATA_DIRECTORY = os.path.join(DATA_DIRECTORY, 'raw')
OUTPUT_FILE_PATH = os.path.join(RAW_DATA_DIRECTORY, 'dados_de_estoque_compilado.json')
LAST_SYNC_FILE_PATH = os.path.join(DATA_DIRECTORY, 'last_sync_estoque.txt')

# --- FUNÇÕES AUXILIARES PARA SINCRONIZAÇÃO ---
def get_last_sync_date() -> str | None:
    """Lê a data da última sincronização bem-sucedida do arquivo."""
    try:
        with open(LAST_SYNC_FILE_PATH, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print("Arquivo de última sincronização não encontrado. Buscando todos os dados.")
        return None

def save_last_sync_date(sync_time: str):
    """Salva a data/hora da sincronização atual para ser usada na próxima execução."""
    os.makedirs(DATA_DIRECTORY, exist_ok=True)
    with open(LAST_SYNC_FILE_PATH, 'w', encoding='utf-8') as f:
        f.write(sync_time)
    print(f"Data de sincronização salva para a próxima execução: {sync_time}")

# ... (início do arquivo src/modules/stock_fetcher.py) ...

def fetch_and_save_stock_data():
    """
    Busca dados de estoque de forma massiva e paginada, utilizando a data da
    última sincronização para obter apenas os registros mais recentes.
    """
    if not (token := get_auth_token()):
        print("❌ Falha na autenticação. A execução será interrompida.")
        return

    dados_compilados = []
    # ALTERAÇÃO 1: Remova o CodFilial daqui. Ele agora irá para a URL.
    auth_headers = {"Authorization": f"Token {token}"}
    
    last_sync = get_last_sync_date()
    data_ate = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    
    pagina = 1
    print("🚀 Iniciando busca de dados de estoque...")

    while True:
        endpoint = f"{BASE_URL}/v2/estoque/{pagina}"
        
        # ALTERAÇÃO 2: Adicione o FILIAL diretamente ao dicionário de parâmetros.
        params = {
            'codfilial': str(FILIAL)
        }
        
        # Adiciona os parâmetros de data, se houver uma sincronização anterior.
        if last_sync:
            params['datade'] = last_sync
            params['dataate'] = data_ate
        
        timestamp = str(int(time.time()))
        signature = generate_signature('get', timestamp)
        
        headers = {
            **auth_headers,
            "Timestamp": timestamp,
            "Signature": signature
        }
        
        print(f"DEBUG: Enviando requisição para página {pagina} com parâmetros: {params}")
        
        try:
            # ... (o resto do código continua exatamente o mesmo) ...
            # 5. Requisição: Faz a chamada à API.
            response = requests.get(endpoint, headers=headers, params=params, timeout=45)
            response.raise_for_status()  # Lança exceção para erros HTTP (ex: 403 Forbidden, 500 Server Error)
            data = response.json()

            # 6. Condição de Parada: Verifica se a API sinalizou o fim dos dados.
            if not data.get("sucesso") or not data.get("dados") or data.get("tipo") == "FIM_DE_PAGINA":
                print("Fim da paginação ou não há mais dados para buscar.")
                break
            
            # 7. Coleta de Dados: Adiciona os dados encontrados à lista principal.
            dados_compilados.extend(data.get("dados", []))
            pagina += 1
            time.sleep(0.1)  # Pausa educada para não sobrecarregar a API.

        except requests.exceptions.RequestException as e:
            print(f"❌ Erro de rede na página {pagina}: {e}")
            return # Interrompe tudo para não salvar uma data de sync incorreta.
        except json.JSONDecodeError:
            print(f"❌ Erro ao decodificar a resposta JSON da página {pagina}.")
            return

    # 8. Salvamento: Após o loop, salva os dados compilados (se houver algum).
    if dados_compilados:
        os.makedirs(RAW_DATA_DIRECTORY, exist_ok=True)
        with open(OUTPUT_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(dados_compilados, f, ensure_ascii=False, indent=4)
        print(f"✅ Sucesso! {len(dados_compilados)} novos registros de estoque salvos em {OUTPUT_FILE_PATH}")
    else:
        print("ℹ️ Nenhum dado novo de estoque foi encontrado desde a última sincronização.")
    
    # 9. Atualização da Sincronização: Salva a data de 'até' para a próxima execução.
    # Isso acontece mesmo que não venham dados novos, para que a próxima busca comece a partir de agora.
    save_last_sync_date(data_ate)