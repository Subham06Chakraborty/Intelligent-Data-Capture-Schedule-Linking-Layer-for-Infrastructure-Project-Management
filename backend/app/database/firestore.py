import os
import json

_db = None
_USE_LOCAL = False


def get_db():
    """
    Returns Firestore client OR a local in-memory mock (for development without Firebase).
    Set USE_LOCAL_DB=true in .env to use the mock.
    """
    global _db, _USE_LOCAL

    if _db is not None:
        return _db

    use_local = os.environ.get("USE_LOCAL_DB", "false").lower() == "true"

    if use_local:
        _USE_LOCAL = True
        _db = _LocalFirestoreDB()
        print("[DB] Using LOCAL in-memory database (no Firebase needed)")
        return _db

    # Real Firebase (Direct Google Cloud Client)
    try:
        from google.cloud import firestore
        from google.oauth2 import service_account

        cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "linked-project-management")

        if cred_path and os.path.exists(cred_path):
            creds = service_account.Credentials.from_service_account_file(cred_path)
            _db = firestore.Client(project=project_id, credentials=creds)
        else:
            _db = firestore.Client(project=project_id)

        print("[DB] Connected to Firebase Firestore (via Native Client)")

    except Exception as e:
        print(f"[DB] Firebase failed ({e}), falling back to local DB")
        _USE_LOCAL = True
        _db = _LocalFirestoreDB()

    return _db


# Alias for backward compatibility
get_firestore_client = get_db


# ─────────────────────────────────────────────────────────────────────────────
# LOCAL IN-MEMORY DATABASE — works without Firebase for development/demo
# Behaves like Firestore client (collection/document/stream/set/get/update)
# ─────────────────────────────────────────────────────────────────────────────
class _LocalDoc:
    def __init__(self, data: dict, doc_id: str):
        self._data = data
        self.exists = data is not None
        self.id = doc_id

    def to_dict(self):
        return self._data or {}


class _LocalCollection:
    def __init__(self, store: dict, name: str):
        self._store = store
        self._name = name
        self._filters = []
        self._order = None
        self._limit_val = None
    def document(self, doc_id: str = None):
        if doc_id is None:
            import uuid
            doc_id = str(uuid.uuid4())
        return _LocalDocRef(self._store, self._name, doc_id)

    def where(self, field: str, op: str, value):
        clone = _LocalCollection(self._store, self._name)
        clone._filters = self._filters + [(field, op, value)]
        clone._order = self._order
        clone._limit_val = self._limit_val
        return clone

    def order_by(self, field: str, direction=None):
        clone = _LocalCollection(self._store, self._name)
        clone._filters = self._filters
        clone._order = field
        clone._limit_val = self._limit_val
        return clone

    def limit(self, n: int):
        clone = _LocalCollection(self._store, self._name)
        clone._filters = self._filters
        clone._order = self._order
        clone._limit_val = n
        return clone

    def stream(self):
        collection = self._store.get(self._name, {})
        docs = list(collection.items())

        for (field, op, value) in self._filters:
            if op == "==":
                docs = [(k, v) for k, v in docs if v.get(field) == value]

        if self._order:
            docs = sorted(docs, key=lambda kv: kv[1].get(self._order, ""))

        if self._limit_val:
            docs = docs[: self._limit_val]

        return [_LocalDoc(v, k) for k, v in docs]

    def add(self, data: dict):
        import uuid
        doc_id = str(uuid.uuid4())
        if self._name not in self._store:
            self._store[self._name] = {}
        self._store[self._name][doc_id] = data
        return _LocalDocRef(self._store, self._name, doc_id)


class _LocalDocRef:
    def __init__(self, store: dict, collection: str, doc_id: str):
        self._store = store
        self._collection = collection
        self._doc_id = doc_id

    @property
    def id(self):
        return self._doc_id

    def set(self, data: dict):
        if self._collection not in self._store:
            self._store[self._collection] = {}
        self._store[self._collection][self._doc_id] = data

    def get(self):
        data = self._store.get(self._collection, {}).get(self._doc_id)
        return _LocalDoc(data, self._doc_id)

    def update(self, data: dict):
        if self._collection not in self._store:
            self._store[self._collection] = {}
        existing = self._store[self._collection].get(self._doc_id, {})
        existing.update(data)
        self._store[self._collection][self._doc_id] = existing

    def delete(self):
        self._store.get(self._collection, {}).pop(self._doc_id, None)


class _LocalFirestoreDB:
    """In-memory Firestore mock. Data lives in RAM — resets on server restart."""
    def __init__(self):
        self._store: dict = {}

    def collection(self, name: str) -> _LocalCollection:
        return _LocalCollection(self._store, name)
