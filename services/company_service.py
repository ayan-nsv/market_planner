import uuid
import gc
import time
from services.gemini_service import generate_image
from services.firebase_service import upload_image, save_url_to_db
from utils.logger import setup_logger

logger = setup_logger("marketing-app")

async def process_company(planner_info: dict) -> str:
    image_bytes = None
    try:
        total_t0 = time.perf_counter()
        # Generate a unique ID for this content
        content_id = str(uuid.uuid4())
        
        # Generate image using Gemini
        gen_t0 = time.perf_counter()
        result = await generate_image(planner_info)
        if not result:
            raise RuntimeError(f"Image generation failed for company {planner_info.get('name', 'Unknown')}")
        image_bytes, mime_type = result
        gen_ms = int((time.perf_counter() - gen_t0) * 1000)

        # Sanity check image size; guard against corrupt/empty results
        if not image_bytes or len(image_bytes) < 1024:  # <1 KB is almost certainly invalid
            raise RuntimeError("Generated image appears invalid or truncated (size < 1KB)")

        # Create storage path with the generated content ID
        company_id = planner_info.get('company_id', 'unknown')
        # Choose file extension based on mime type
        ext_map = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/webp": ".webp",
        }
        file_ext = ext_map.get(mime_type, ".png")
        path = f"content/{company_id}/{content_id}{file_ext}"
        
        # Upload image to Firebase Storage (this function will handle cleanup)
        upload_t0 = time.perf_counter()
        url = await upload_image(image_bytes, path, content_type=mime_type)
        upload_ms = int((time.perf_counter() - upload_t0) * 1000)

        # Clear image bytes from memory immediately after upload
        del image_bytes
        image_bytes = None
        gc.collect()

        # Save metadata to Firestore with additional info
        additional_data = {
            "company_id": planner_info.get('company_id'),
            "channel": planner_info.get('channel'),
        }

        channel = planner_info["channel"].lower()
        company_id = planner_info.get('company_id')
        # await save_url_to_db(content_id, url, channel, company_id, additional_data)
        
        total_ms = int((time.perf_counter() - total_t0) * 1000)
        logger.info(
            f"image_pipeline: company_id={company_id} channel={channel} content_id={content_id} "
            f"bytes={len(url) if isinstance(url, (bytes, bytearray)) else 'n/a'} gen_ms={gen_ms} "
            f"upload_ms={upload_ms} total_ms={total_ms} mime={mime_type} path={path} url={url}"
        )

        return url
        
    except Exception as e:
        if image_bytes is not None:
            del image_bytes
            gc.collect()
        raise e



