from fastapi import APIRouter, HTTPException        
from models.planner_model import PlannerRequest
from config.firebase_config import get_firestore_client
from services.gpt_service import generate_facebook_post, generate_linkedin_post, generate_instagram_post

from services.gpt_service import generate_image_prompt

from utils.logger import setup_logger

router = APIRouter()

logger = setup_logger("marketing-app")


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
        logger.info(
            "Generating LinkedIn planner for company %s with theme '%s'",
            company_id,
            planner.theme_title,
        )
        db = get_firestore_client()
        company_ref = db.collection("companies").document(company_id)
        company_doc = company_ref.get()
        if not company_doc.exists:
            logger.warning("LinkedIn planner request failed: company %s not found", company_id)
            raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
        company_data = company_doc.to_dict()

        generated_planner_data = generate_linkedin_post(company_data, planner.theme_title, planner.theme_description)

        channel = generated_planner_data.get("channel", "").lower().strip()

        # image_prompt = generated_planner_data.get("image_prompt", "")


        caption = generated_planner_data.get("caption", "")
        hashtags = generated_planner_data.get("hashtags", [])
        overlay_text = generated_planner_data.get("overlay_text", "")


        generated_image_prompt = await generate_image_prompt(caption, hashtags, overlay_text)
        image_prompt = generated_image_prompt.get("image_prompt", "")

        final_data = {
                "channel": channel,
                "image_prompt": image_prompt,
                "caption": caption,
                "hashtags": hashtags,
                "overlay_text": overlay_text,
                "company_id": company_id,
        }
        logger.info(
            "LinkedIn planner generated for company %s with channel '%s'",
            company_id,
            channel,
        )
        return final_data
    except HTTPException as http_exc:
        logger.warning(
            "LinkedIn planner generation returned HTTP %s for company %s: %s",
            http_exc.status_code,
            company_id,
            http_exc.detail,
        )
        raise
    except Exception as e:
        logger.exception("Error creating LinkedIn planner for company %s", company_id)
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
        logger.info(
            "Generating Facebook planner for company %s with theme '%s'",
            company_id,
            planner.theme_title,
        )
        db = get_firestore_client()
        company_ref = db.collection("companies").document(company_id)
        company_doc = company_ref.get()
        if not company_doc.exists:
            logger.warning("Facebook planner request failed: company %s not found", company_id)
            raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
        company_data = company_doc.to_dict()

        generated_planner_data = generate_facebook_post(company_data, planner.theme_title, planner.theme_description)

        channel = generated_planner_data.get("channel", "").lower().strip()

        # image_prompt = generated_planner_data.get("image_prompt", "")

        caption = generated_planner_data.get("caption", "")
        hashtags = generated_planner_data.get("hashtags", [])
        overlay_text = generated_planner_data.get("overlay_text", "")

        generated_image_prompt = await generate_image_prompt(caption, hashtags, overlay_text)
        image_prompt = generated_image_prompt.get("image_prompt", "")

        final_data = {
                "channel": channel,
                "image_prompt": image_prompt,
                "caption": caption,
                "hashtags": hashtags,
                "overlay_text": overlay_text,
                "company_id": company_id,
            }
        logger.info(
            "Facebook planner generated for company %s with channel '%s'",
            company_id,
            channel,
        )
        return final_data
    except HTTPException as http_exc:
        logger.warning(
            "Facebook planner generation returned HTTP %s for company %s: %s",
            http_exc.status_code,
            company_id,
            http_exc.detail,
        )
        raise
    except Exception as e:
        logger.exception("Error creating Facebook planner for company %s", company_id)
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
        logger.info(
            "Generating Instagram planner for company %s with theme '%s'",
            company_id,
            planner.theme_title,
        )
        db = get_firestore_client()
        company_ref = db.collection("companies").document(company_id)
        company_doc = company_ref.get()
        if not company_doc.exists:
            logger.warning("Instagram planner request failed: company %s not found", company_id)
            raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
        company_data = company_doc.to_dict()

        generated_planner_data = generate_instagram_post(company_data, planner.theme_title, planner.theme_description)

        channel = generated_planner_data.get("channel", "").lower().strip()

        # image_prompt = generated_planner_data.get("image_prompt", "")
        
        caption = generated_planner_data.get("caption", "")
        hashtags = generated_planner_data.get("hashtags", [])
        overlay_text = generated_planner_data.get("overlay_text", "")

        generated_image_prompt = await generate_image_prompt(caption, hashtags, overlay_text)
        image_prompt = generated_image_prompt.get("image_prompt", "")
        final_data = {
                "channel": channel,
                "image_prompt": image_prompt,
                "caption": caption,
                "hashtags": hashtags,
                "overlay_text": overlay_text,
                "company_id": company_id,
            }
        logger.info(
            "Instagram planner generated for company %s with channel '%s'",
            company_id,
            channel,
        )
        return final_data
    except HTTPException as http_exc:
        logger.warning(
            "Instagram planner generation returned HTTP %s for company %s: %s",
            http_exc.status_code,
            company_id,
            http_exc.detail,
        )
        raise
    except Exception as e:
        logger.exception("Error generating Instagram planner for company %s", company_id)
        raise HTTPException(status_code= 500, detail=f"Error generating facebook planner: {str(e)}")

