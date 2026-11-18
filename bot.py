import time
import random
import requests

URL = ""
MAX_VISITS = 20

session = requests.Session()
session.headers.update({
    "User-Agent": "LoadTestBot/1.0 (Internal Testing)"
})

for i in range(1, MAX_VISITS + 1):
    try:
        response = session.get(URL, timeout=5)
        print(f"Besuch {i}/{MAX_VISITS} - Status: {response.status_code}")

        if response.status_code in (429, 500, 502, 503, 504):
            print("Server meldet Überlastung - Test wird zum Schutz abgebrochen.")
            break

    except requests.exceptions.RequestException as e:
        print(f"Verbindungsfehler: {e}")
        break

    time.sleep(random.uniform(1.0, 3.0))