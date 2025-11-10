from fastapi import APIRouter, HTTPException
from google.cloud import firestore
from config.firebase_config import get_firestore_client
from utils.logger import setup_logger
from models.schedular_model import SchedularRequest

from datetime import datetime

logger = setup_logger("marketing-app")
router = APIRouter()
db = get_firestore_client()


@router.post("/schedule/{company_id}/create")
def schedule_post(company_id: str, schedular: SchedularRequest):
    try:
        company_ref = db.collection("companies").document(company_id)
        company = company_ref.get()

        if not company.exists:
            raise HTTPException(status_code=404, detail=f"  coudn't find the company")
        company_data = company.to_dict()

        # validate the post data
        if not any([
            schedular.instagram_post_count,
            schedular.facebook_post_count,
            schedular.linkedin_post_count
        ]):
            raise HTTPException(status_code=400, detail="At least one post count is required")
        if not schedular.theme:
            raise HTTPException(status_code=400, detail=f"  theme is required")
        if not schedular.theme_description:
            raise HTTPException(status_code=400, detail=f"  theme description is required")


        post_data = {
            "theme":schedular.theme,
            "theme_description": schedular.theme_description,
            "instagram_post_count": schedular.instagram_post_count,
            "facebook_post_count": schedular.facebook_post_count,
            "linkedin_post_count": schedular.linkedin_post_count,
            }

        
        final_data = {
            "post_data" : post_data,
            "status": "pending",
            "company_id": company_id,
            "month_id": schedular.month_id,
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP
        }
        doc_ref = db.collection("scheduled_posts").document(company_id).collection("posts").add(final_data)
        return {
            "status": "pending",
            "id": doc_ref[1].id,
            "message": f"Post scheduled successfully for company {company_data.get('name', company_id)}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Couldn't create post for {company_id}: {str(e)}")
    

