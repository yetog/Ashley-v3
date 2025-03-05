import requests
from src.config import IONOS_API_TOKEN, MODEL_NAME, ENDPOINT

def query_ionos(prompt):
    headers = {
        "Authorization": f"Bearer {IONOS_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    body = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 512
    }
    
    response = requests.post(ENDPOINT, json=body, headers=headers)
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error {response.status_code}: {response.text}"
