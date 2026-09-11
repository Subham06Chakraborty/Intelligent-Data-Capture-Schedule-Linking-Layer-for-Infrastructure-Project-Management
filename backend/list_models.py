import os, requests
from dotenv import load_dotenv
load_dotenv()

key = os.environ.get("GROQ_API_KEY")
res = requests.get('https://api.groq.com/openai/v1/models', headers={'Authorization': f'Bearer {key}'}).json()
for m in res.get('data', []):
    print(m['id'])
