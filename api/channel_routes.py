from fastapi import APIRouter, HTTPException
from google.cloud import firestore

from fastapi import Depends
from config.firebase_config import get_firestore_client

from utils.logger import setup_logger

from models.channel_model import ChannelConfigRequest

logger = setup_logger("marketing-app")

router = APIRouter()


async def get_db():
    return get_firestore_client()


###################################################### configure channel ##################################################
@router.post("/channel/{company_id}/config")
def configure_channel(company_id: str, channel_config: ChannelConfigRequest, db: firestore.Client = Depends(get_db)):
    try:
        save_data = {
            "company_id": company_id,
            "instagram_post_count": channel_config.instagram_post_count,
            "facebook_post_count": channel_config.facebook_post_count,
            "linkedin_post_count": channel_config.linkedin_post_count,
            "email_campaign_count": channel_config.email_campaign_count,
            "blog_post_count": channel_config.blog_post_count,

            "instagram_active": channel_config.instagram_active,
            "facebook_active": channel_config.facebook_active,
            "linkedin_active": channel_config.linkedin_active,
            "email_campaign_active": channel_config.email_campaign_active,
            "blog_post_active": channel_config.blog_post_active,
            
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP
        }
        doc_ref = db.collection("channel_config").document(company_id)
        doc_ref.set(save_data, merge=True)
        logger.info(f"Channels configured successfully for company {company_id}")
        return {
            "status": "success",
            "message": "Channels configured successfully",
            "company_id": doc_ref.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring channel for company {company_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error configuring channel: {str(e)}")


###################################################### get channel config ##################################################
@router.get("/channel/{company_id}/config")
def get_channel_config(company_id: str, db: firestore.Client = Depends(get_db)):
    try:
        doc_ref = db.collection("channel_config").document(company_id).get()
        if not doc_ref.exists:
            raise HTTPException(status_code=404, detail=f"Channel config not found for company {company_id}")
        
        logger.info(f"Channel config fetched successfully for company {company_id}")
        return doc_ref.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting channel config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting channel config: {str(e)}")