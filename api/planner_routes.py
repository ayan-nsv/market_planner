from fastapi import APIRouter, HTTPException
from grpc import StatusCode
from models.planner_model import PlannerRequest, PlannerUpdateRequest
from google.cloud import firestore
from config.firebase_config import get_firestore_client
from services.gpt_service import generate_facebook_post, generate_linkedin_post, generate_all_posts, generate_instagram_post

router = APIRouter()



######## create linkedin planner
@router.post(
    "/planners/{company_id}/linkedin",
    tags=["LinkedIn Planners"],
    summary="Generate LinkedIn planner",
    description="Generate a social media planner specifically for LinkedIn platform",
    response_description="Generated LinkedIn planner details"
)
async def generate_linkedin_planner(planner: PlannerRequest, company_id: str):
    try:
        db = get_firestore_client()
        company_ref = db.collection("companies").document(company_id)
        company_doc = company_ref.get()
        if not company_doc.exists:
            raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
        company_data = company_doc.to_dict()

        generated_planner_data = generate_linkedin_post(company_data, planner.theme_title, planner.theme_description)

        channel = generated_planner_data.get("channel", "").lower().strip()

        image_prompt = generated_planner_data.get("image_prompt", "")
        caption = generated_planner_data.get("caption", "")
        hashtags = generated_planner_data.get("hashtags", [])
        overlay_text = generated_planner_data.get("overlay_text", "")

        final_data = {
                "channel": channel,
                "image_prompt": image_prompt,
                "caption": caption,
                "hashtags": hashtags,
                "overlay_text": overlay_text,
                "company_id": company_id,
        }
            
        return final_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code= 500, detail=f"Error creating linkedin planner: {str(e)}")

##### create facebook planner
@router.post(
    "/planners/{company_id}/facebook",
    tags=["Facebook Planners"],
    summary="Generate Facebook planner",
    description="Generate a social media planner specifically for Facebook platform",
    response_description="Generated Facebook planner details"
)
async def generate_facebook_planner(planner: PlannerRequest, company_id: str):
    try:
        db = get_firestore_client()
        company_ref = db.collection("companies").document(company_id)
        company_doc = company_ref.get()
        if not company_doc.exists:
            raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
        company_data = company_doc.to_dict()

        generated_planner_data = generate_facebook_post(company_data, planner.theme_title, planner.theme_description)

        channel = generated_planner_data.get("channel", "").lower().strip()

        image_prompt = generated_planner_data.get("image_prompt", "")
        caption = generated_planner_data.get("caption", "")
        hashtags = generated_planner_data.get("hashtags", [])
        overlay_text = generated_planner_data.get("overlay_text", "")

        final_data = {
                "channel": channel,
                "image_prompt": image_prompt,
                "caption": caption,
                "hashtags": hashtags,
                "overlay_text": overlay_text,
                "company_id": company_id,
            }
            
        return final_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code= 500, detail=f"Error creating facebook planner: {str(e)}")

###### create instagram planner
@router.post(
    "/planners/{company_id}/instagram",
    tags=["Instagram Planners"],
    summary="Generate Instagram planner",
    description="Generate a social media planner specifically for Instagram platform",
    response_description="Generated Instagram planner details"
)
async def generate_instagram_planner(planner: PlannerRequest, company_id: str):
    try:
        db = get_firestore_client()
        company_ref = db.collection("companies").document(company_id)
        company_doc = company_ref.get()
        if not company_doc.exists:
            raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
        company_data = company_doc.to_dict()

        generated_planner_data = generate_instagram_post(company_data, planner.theme_title, planner.theme_description)

        channel = generated_planner_data.get("channel", "").lower().strip()

        image_prompt = generated_planner_data.get("image_prompt", "")
        caption = generated_planner_data.get("caption", "")
        hashtags = generated_planner_data.get("hashtags", [])
        overlay_text = generated_planner_data.get("overlay_text", "")

        final_data = {
                "channel": channel,
                "image_prompt": image_prompt,
                "caption": caption,
                "hashtags": hashtags,
                "overlay_text": overlay_text,
                "company_id": company_id,
            }
        return final_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code= 500, detail=f"Error generating facebook planner: {str(e)}")

