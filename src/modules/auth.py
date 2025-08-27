# src/modules/auth.py
import requests
import hmac
import hashlib
import base64
import time

#BASE_URL = "http://127.0.0.1:60500"
BASE_URL = "http://192.168.1.111:60000"
#BASE_URL = "http://201.22.86.125:60000"
SENHA = "V7!xL9@qP#zR2$wM"
SERIE = "HIEAPA-605662-FWKD"
FILIAL = 1

def generate_signature(method: str, timestamp: str, body_content: str = "") -> str:
    base64_body = base64.b64encode(body_content.encode('utf-8')).decode('utf-8') if body_content else ""
    raw_signature = f"{method.lower()}{timestamp}{base64_body}"
    hashed = hmac.new(SENHA.encode('utf-8'), raw_signature.encode('utf-8'), hashlib.sha256).digest()
    return base64.b64encode(hashed).decode('utf-8')

def get_auth_token() -> str | None:
    endpoint = f"{BASE_URL}/auth/"
    timestamp = str(int(time.time()))
    signature = generate_signature('get', timestamp)

    headers = {
        "Signature": signature,
        "Timestamp": timestamp,
        "CodFilial": str(FILIAL),
    }
    params = {"serie": SERIE, "codfilial": FILIAL}

    try:
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        response_data = response.json()

        if response_data.get("sucesso"):
            return response_data.get("dados", {}).get("token")
        print(f"Falha na autenticação: {response_data.get('mensagem', 'Erro desconhecido')}")
    except Exception as e:
        print(f"Erro na autenticação: {e}")
    return None