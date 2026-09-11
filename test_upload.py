import requests

url = "http://localhost:8000/api/v1/ingest/upload"
files = {'file': ('sample_dpr.txt', open('sample_dpr.txt', 'rb'), 'text/plain')}
data = {'project_id': 'test_project_id', 'uploaded_by': 'site_engineer'}

try:
    response = requests.post(url, files=files, data=data)
    print("Status:", response.status_code)
    print("JSON:", response.json())
except Exception as e:
    print("Error:", e)
