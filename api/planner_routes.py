from fastapi import APIRouter, HTTPException        
from models.planner_model import PlannerRequest, CaptionRegenerateRequest
from services.gpt_service import generate_facebook_post, generate_linkedin_post, generate_instagram_post, regenerate_caption

from fastapi import Depends
from google.cloud import firestore
from config.firebase_config import get_firestore_client

from services.gpt_service import generate_image_prompt

from utils.logger import setup_logger

router = APIRouter()

logger = setup_logger("marketing-app")

async def get_db():
    return get_firestore_client()


######## create linkedin planner
@router.post(
    "/planners/{company_id}/linkedin",
    tags=["LinkedIn Planners"],
    summary="Generate LinkedIn planner",
    description="Generate a social media planner specifically for LinkedIn platform",
    response_description="Generated LinkedIn planner details"
)
async def generate_linkedin_planner(planner: PlannerRequest, company_id: str, db: firestore.Client = Depends(get_db)):
    try:
        logger.info(
            "Generating LinkedIn planner for company %s with theme '%s'",
            company_id,
            planner.theme_title,
        )
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

        image_analysis = {
                "composition_and_style": company_data.get("composition_and_style", ""),
                "environment_settings": company_data.get("environment_settings", ""),
                "image_types_and_animation": company_data.get("image_types_and_animation", ""),
                "keywords_for_ai_image_generation": company_data.get("keywords_for_ai_image_generation", ""),
                "lighting_and_color_tone": company_data.get("lighting_and_color_tone", ""),
                "subjects_and_people": company_data.get("subjects_and_people", ""),
                "technology_elements": company_data.get("technology_elements", ""),
                "theme_and_atmosphere": company_data.get("theme_and_atmosphere", ""),
            }

        generated_image_prompt = await generate_image_prompt(caption, hashtags, overlay_text, image_analysis)
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
async def generate_facebook_planner(planner: PlannerRequest, company_id: str, db: firestore.Client = Depends(get_db)):
    try:
        logger.info(
            "Generating Facebook planner for company %s with theme '%s'",
            company_id,
            planner.theme_title,
        )
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

        # image generation according to image analysis 
        image_analysis = {
                "composition_and_style": company_data.get("composition_and_style", ""),
                "environment_settings": company_data.get("environment_settings", ""),
                "image_types_and_animation": company_data.get("image_types_and_animation", ""),
                "keywords_for_ai_image_generation": company_data.get("keywords_for_ai_image_generation", ""),
                "lighting_and_color_tone": company_data.get("lighting_and_color_tone", ""),
                "subjects_and_people": company_data.get("subjects_and_people", ""),
                "technology_elements": company_data.get("technology_elements", ""),
                "theme_and_atmosphere": company_data.get("theme_and_atmosphere", ""),
            }
        generated_image_prompt = await generate_image_prompt(caption, hashtags, overlay_text, image_analysis)
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
async def generate_instagram_planner(planner: PlannerRequest, company_id: str, db: firestore.Client = Depends(get_db)):
    try:
        logger.info(
            "Generating Instagram planner for company %s with theme '%s'",
            company_id,
            planner.theme_title,
        )
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

        image_analysis = {
                "composition_and_style": company_data.get("composition_and_style", ""),
                "environment_settings": company_data.get("environment_settings", ""),
                "image_types_and_animation": company_data.get("image_types_and_animation", ""),
                "keywords_for_ai_image_generation": company_data.get("keywords_for_ai_image_generation", ""),
                "lighting_and_color_tone": company_data.get("lighting_and_color_tone", ""),
                "subjects_and_people": company_data.get("subjects_and_people", ""),
                "technology_elements": company_data.get("technology_elements", ""),
                "theme_and_atmosphere": company_data.get("theme_and_atmosphere", ""),
            }


        generated_image_prompt = await generate_image_prompt(caption, hashtags, overlay_text, image_analysis)
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


######################################################### caption regenerate #########################################################

@router.post(
    "/planners/caption/regenerate",
    tags=["Caption Regenerate"],
    summary="Regenerate caption",
    description="Regenerate caption for a social media post using the same image prompt, hashtags and overlay text",
    response_description="Regenerated caption"
)
async def regenerate_caption_route(caption_regenerate: CaptionRegenerateRequest):
    try:
        generated_caption = await regenerate_caption(caption_regenerate.caption, caption_regenerate.hashtags, caption_regenerate.overlay_text)

        if not generated_caption:
            raise HTTPException(status_code=400, detail="Failed to regenerate caption")
            
        return {"caption": generated_caption.get("caption", "")}
    except HTTPException as e:
        raise
    except Exception as e:
        logger.exception("Error regenerating caption for planner")
        raise HTTPException(status_code= 500, detail=f"Error regenerating caption: {str(e)}")