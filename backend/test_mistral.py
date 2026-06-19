import requests
import os
from dotenv import load_dotenv
load_dotenv()

r = requests.post(
    "https://router.huggingface.co/together/v1/chat/completions",
    headers={"Authorization": f"Bearer {os.getenv('HF_API_KEY')}"},
    json={
        "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "messages": [{"role": "user", "content": "Write one sentence about Nepal remittance."}]
    }
)
print(r.status_code)
print(r.json())