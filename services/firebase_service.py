
import os
from config.firebase_config import get_firebase_client
import tempfile
import os as _os

from dotenv import load_dotenv
from utils.logger import setup_logger

load_dotenv()

logger = setup_logger("marketing-app")

storage_client, db = get_firebase_client()


async def upload_image(image_bytes: bytes, path: str, content_type: str = "image/png") -> str:
    try:
        bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")
        if not bucket_name:
            raise Exception("No Bucket found!")
        
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(path)

        # Reduce peak memory by streaming from a temporary file with controlled chunk size
        # 1MB chunks limit RAM spikes across concurrent requests
        blob.chunk_size = 1 * 1024 * 1024

        tmp_file = None
        try:
            tmp_file = tempfile.NamedTemporaryFile(delete=False)
            tmp_file.write(image_bytes)
            tmp_file.flush()
            tmp_file.close()

            blob.upload_from_filename(tmp_file.name, content_type=content_type)
        finally:
            if tmp_file is not None:
                try:
                    _os.unlink(tmp_file.name)
                except Exception:
                    pass
        
        encoded_path = path.replace('/', '%2F')
        public_url = f"https://firebasestorage.googleapis.com/v0/b/{bucket_name}/o/{encoded_path}?alt=media"
        
        logger.info(f"Image uploaded successfully to: {path}")
        return public_url
        
    except Exception as e:
        logger.error(f"Failed to upload image to {path}: {str(e)}")
        raise Exception(f"Upload failed: {str(e)}")



