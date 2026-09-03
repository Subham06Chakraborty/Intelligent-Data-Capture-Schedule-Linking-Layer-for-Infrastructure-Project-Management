"""Firestore client setup for ProjectBridge.

The Google libraries are imported lazily so the API can still start for
health checks/tests when Firestore dependencies or credentials are not set up.
"""
from functools import lru_cache

from app.config import settings






@lru_cache(maxsize=1)
def get_firestore_client():
    """Create one Firestore client and reuse it for the process."""
    try:
        from google.cloud import firestore
        from google.oauth2 import service_account
    except ImportError as exc:
        raise RuntimeError(
            "Firestore dependencies are missing. Run: pip install -r requirements.txt"
        ) from exc

    if settings.GOOGLE_APPLICATION_CREDENTIALS:
        credentials = service_account.Credentials.from_service_account_file(
            settings.GOOGLE_APPLICATION_CREDENTIALS
        )
        return firestore.Client(
            project=settings.GOOGLE_CLOUD_PROJECT or None,
            credentials=credentials,
        )

    return firestore.Client(project=settings.GOOGLE_CLOUD_PROJECT or None)
