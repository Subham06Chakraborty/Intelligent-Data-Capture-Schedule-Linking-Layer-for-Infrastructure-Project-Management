import os
from dotenv import load_dotenv

load_dotenv("D:\\New folder (8)\\backend\\.env")

print("Creds path:", os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))

try:
    import firebase_admin
    from firebase_admin import credentials, firestore

    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    
    print("Firestore client initialized successfully!")
    
    # Try a simple write
    db.collection("test").document("test_doc").set({"hello": "world"})
    print("Firestore write successful!")
    
    # Try a simple read
    doc = db.collection("test").document("test_doc").get()
    print("Firestore read successful!", doc.to_dict())

except Exception as e:
    print("ERROR:", e)
    import traceback
    traceback.print_exc()
