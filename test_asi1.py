import requests, os
from dotenv import load_dotenv
load_dotenv()

resp = requests.post(
    "https://api.asi1.ai/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {os.getenv('ASI_ONE_API_KEY')}",
        "Content-Type": "application/json"
    },
    json={"model": "asi1", "messages": [{"role": "user", "content": "Say hi"}]}
)
print(resp.status_code)
print(resp.json())
