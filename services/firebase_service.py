import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from config.firebase_config import get_firebase_client

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

storage_client, db = get_firebase_client()


async def upload_image(image_bytes: bytes, path: str, content_type: str = "image/png") -> str:
    try:
        bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")
        if not bucket_name:
            raise Exception("No Bucket found!")
        
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(path)
        
        # Upload the file
        blob.upload_from_string(image_bytes, content_type=content_type)
        
        encoded_path = path.replace('/', '%2F')
        public_url = f"https://firebasestorage.googleapis.com/v0/b/{bucket_name}/o/{encoded_path}?alt=media"
        
        logger.info(f"Image uploaded successfully to: {path}")
        return public_url
        
    except Exception as e:
        logger.error(f"Failed to upload image to {path}: {str(e)}")
        raise Exception(f"Upload failed: {str(e)}")


async def save_url_to_db(content_id: str, image_url: str, channel: str, company_id: str, additional_data: Optional[Dict[str, Any]] = None):
   
    try:
        collection_name = f"{channel}_posts"
        doc_ref = db.collection(collection_name).document(company_id).collection("image").document(content_id)
        
        # Prepare update data
        update_data = {
            "img_url": image_url,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        if additional_data:
            update_data.update(additional_data)
        
        doc_ref.set(update_data)
        
        logger.info(f"Image metadata saved for images/{content_id}")
        
    except Exception as e:
        logger.error(f"Failed to save image metadata for images/{content_id}: {str(e)}")
        raise Exception(f"Metadata save failed: {str(e)}")



async def create_content_record(content_data: Dict[str, Any]) -> str:
    try:
        content_data.update({
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })
        
        doc_ref = db.collection("images").add(content_data)
        content_id = doc_ref[1].id
        
        logger.info(f"Content record created: {content_id}")
        return content_id
        
    except Exception as e:
        logger.error(f"Failed to create content record: {str(e)}")
        raise Exception(f"Content creation failed: {str(e)}")

async def get_document(collection: str, document_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a document from Firestore
    """
    try:
        doc_ref = db.collection(collection).document(document_id)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            data["id"] = doc.id
            return data
        return None
        
    except Exception as e:
        logger.error(f"Failed to get document {collection}/{document_id}: {str(e)}")
        raise Exception(f"Document fetch failed: {str(e)}")

async def update_document(collection: str, document_id: str, data: Dict[str, Any]):
    """
    Update a document in Firestore
    """
    try:
        doc_ref = db.collection(collection).document(document_id)
        data["updated_at"] = datetime.now(timezone.utc)
        doc_ref.update(data)
        
        logger.info(f"Document updated: {collection}/{document_id}")
        
    except Exception as e:
        logger.error(f"Failed to update document {collection}/{document_id}: {str(e)}")
        raise Exception(f"Document update failed: {str(e)}")

async def delete_document(collection: str, document_id: str):
    """
    Delete a document from Firestore
    """
    try:
        doc_ref = db.collection(collection).document(document_id)
        doc_ref.delete()
        
        logger.info(f"Document deleted: {collection}/{document_id}")
        
    except Exception as e:
        logger.error(f"Failed to delete document {collection}/{document_id}: {str(e)}")
        raise Exception(f"Document deletion failed: {str(e)}")