import requests

BASE_URL = "http://localhost:8002"

def test_ping():
    response = requests.get(f"{BASE_URL}/")
    print("Ping:", response.status_code, response.json())

def test_status():
    response = requests.get(f"{BASE_URL}/status")
    print("Status:", response.status_code, response.json())

def test_recomendar_dummy():
    payload = {
        "partner_id": 3,
        "top_n": 5,
        "user": "test_user"
    }
    response = requests.post(f"{BASE_URL}/recomendar", json=payload)
    print("Recomendar:", response.status_code)
    try:
        print(response.json())
    except Exception:
        print(response.text)

if __name__ == "__main__":
    test_ping()
    test_status()
    test_recomendar_dummy()
