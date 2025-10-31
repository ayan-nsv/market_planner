import uuid
import gc
from services.gemini_service import generate_image
from services.firebase_service import upload_image, save_url_to_db

async def process_company(planner_info: dict) -> str:
    image_bytes = None
    try:
        # Generate a unique ID for this content
        content_id = str(uuid.uuid4())
        
        # Generate image using Gemini
        image_bytes = await generate_image(planner_info)
        if not image_bytes:
            raise RuntimeError(f"Image generation failed for company {planner_info.get('name', 'Unknown')}")

        # Create storage path with the generated content ID
        company_id = planner_info.get('company_id', 'unknown')
        path = f"content/{company_id}/{content_id}.png"
        
        # Upload image to Firebase Storage (this function will handle cleanup)
        url = await upload_image(image_bytes, path)

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
        await save_url_to_db(content_id, url, channel, company_id, additional_data)
        
        return url
        
    except Exception as e:
        if image_bytes is not None:
            del image_bytes
            gc.collect()
        raise e