import os
from dotenv import load_dotenv
load_dotenv()

from google.cloud import firestore
from google.oauth2 import service_account

cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
creds = service_account.Credentials.from_service_account_file(cred_path)

db = firestore.Client(project=os.environ.get("GOOGLE_CLOUD_PROJECT", "linked-project-management"), credentials=creds)

docs = db.collection('projects').limit(1).stream()
print("Success! Docs:", list(docs))
