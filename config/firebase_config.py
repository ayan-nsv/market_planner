# import os
# from google.cloud import storage, firestore

# from dotenv import load_dotenv

# load_dotenv()

# def get_firebase_client():
#     project_id = os.getenv("FIREBASE_PROJECT_ID")
#     storage_client = storage.Client(project=project_id)
#     db = firestore.Client(project=project_id)
#     return storage_client, db

import os
from google.cloud import storage, firestore
from dotenv import load_dotenv

load_dotenv()

# Singleton pattern for clients
_storage_client = None
_db_client = None

def get_firebase_client():
    """
    Returns singleton instances of storage and firestore clients
    to prevent memory leaks from multiple client instances
    """
    global _storage_client, _db_client
    
    project_id = os.getenv("FIREBASE_PROJECT_ID")
    
    if _storage_client is None:
        _storage_client = storage.Client(project=project_id)
    
    if _db_client is None:
        _db_client = firestore.Client(project=project_id)
    
    return _storage_client, _db_client

def get_firestore_client():
    """
    Returns singleton firestore client instance
    """
    global _db_client
    
    if _db_client is None:
        project_id = os.getenv("FIREBASE_PROJECT_ID")
        _db_client = firestore.Client(project=project_id)
    
    return _db_client