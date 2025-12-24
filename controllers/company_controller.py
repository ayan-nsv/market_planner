from services.company_service import process_company
from utils.error_handler import handle_error

async def create_company_image(planner_info: dict):
    try:
        url = await process_company(planner_info)
        return {"status": "success", "image_url": url}
    except Exception as e:
        return handle_error(e)