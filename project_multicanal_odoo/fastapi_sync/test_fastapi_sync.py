import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "http://localhost:8001"  # Asegúrate que coincida con tu docker-compose

# Credenciales
USERNAME = "admin"
PASSWORD = "admin123"

def test_ping():
    url = f"{BASE_URL}/"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    print("Ping:", response.status_code, response.json())

def test_status():
    url = f"{BASE_URL}/status"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    print("Status:", response.status_code, response.json())

def test_crear_pedido():
    url = f"{BASE_URL}/crear_pedido"
    payload = {
        "partner_id": 3,
        "channel_code": "WEB",
        "order_ref": "WEB-PRUEBA-001",
        "order_lines": [
            {"product_id": 1, "quantity": 2},
            {"product_id": 2, "quantity": 1}
        ]
    }
    response = requests.post(url, json=payload, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    print("Crear Pedido:", response.status_code)
    try:
        print(response.json())
    except Exception:
        print(response.text)

if __name__ == "__main__":
    test_ping()
    test_status()
    test_crear_pedido()
