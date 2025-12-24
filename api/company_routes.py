import json
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from models.company_model import CompanyRequest, UsageRequest
from config.firebase_config import get_firestore_client

from api.theme_routes import  generate_all_themes_route

from utils.logger import setup_logger

from cache.redis_config import redis_set, redis_get, redis_delete, json_dumps_firestore


from google.cloud import firestore
from google.cloud.firestore_v1 import DocumentReference, GeoPoint
from google.cloud.firestore_v1._helpers import DatetimeWithNanoseconds


logger = setup_logger("marketing-app")

async def get_db():
    return get_firestore_client()


router = APIRouter()


def convert_firestore_datetimes(data):
    if isinstance(data, dict):
        return {k: convert_firestore_datetimes(v) for k, v in data.items()}

    if isinstance(data, list):
        return [convert_firestore_datetimes(item) for item in data]

    # Firestore datetime -> ISO string
    if isinstance(data, (DatetimeWithNanoseconds, datetime)):
        return data.isoformat()

    # Optional: Handle Firestore GeoPoints
    if isinstance(data, GeoPoint):
        return {"latitude": data.latitude, "longitude": data.longitude}

    # Optional: Handle Firestore DocumentReference
    if isinstance(data, DocumentReference):
        return data.path

    return data




@router.get("/company")
def get_companies(db: firestore.Client = Depends(get_db), page: int = 1, limit: int = 5):
    try:
        companies_ref = db.collection("companies")
        docs = companies_ref.limit(limit).offset((page-1)*limit).stream()
        companies = [{**doc.to_dict(), "id": doc.id} for doc in docs]
        # Convert Firestore datetime objects to ISO strings for JSON serialization
        companies = [convert_firestore_datetimes(company) for company in companies]
        logger.info(f"Companies fetched successfully")
        return {
            "data": companies,
            "page": page,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error fetching companies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching companies: {str(e)}")



@router.post("/company")
async def create_company(company: CompanyRequest, db: firestore.Client = Depends(get_db)):
    try:
        
        if not company.company_name or not company.company_name.strip():
            raise HTTPException(status_code=400, detail="Company name is required")
        
        existing_companies = db.collection("companies")\
            .where("company_name", "==", company.company_name)\
            .limit(1)\
            .get()
            
        if existing_companies:
            raise HTTPException(
                status_code=400, 
                detail=f"Company with name '{company.company_name}' already exists"
            )

        company_data = {
            "url": company.url or "",
            "address": company.address or "",
            "industry": company.industry or "",
            "keywords": company.keywords or [],
            "logo_url": company.logo_url or "",
            "products": company.products or [],
            "favicon_url": company.favicon_url or "",
            "company_name": company.company_name,
            "company_info": company.company_info or "",
            "target_group": company.target_group or "",
            "theme_colors": company.theme_colors or [],
            "tone_analysis": company.tone_analysis or "",
            "matched_fonts": company.matched_fonts or {},
            "fonts_typography": company.fonts_typography or [],
            "product_categories": company.product_categories or {},

            "analyzed_images": company.analyzed_images or [],
            "subjects_and_people": company.subjects_and_people or "",
            "technology_elements": company.technology_elements or "",
            "theme_and_atmosphere": company.theme_and_atmosphere or "",
            "environment_settings": company.environment_settings or "",
            "composition_and_style": company.composition_and_style or "",
            "lighting_and_color_tone": company.lighting_and_color_tone or "",
            "image_types_and_animation": company.image_types_and_animation or "",
            "keywords_for_ai_image_generation": company.keywords_for_ai_image_generation or "",
            "image_urls": company.image_urls or [],

            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP    
        }
        doc_ref = db.collection("companies").add(company_data)
        logger.info(f"Company '{company.company_name}' created successfully: {doc_ref[1].id}")

        # Note: company_data contains SERVER_TIMESTAMP placeholders, so we don't cache immediately
        # The data will be cached when fetched via get_company endpoint
        company_id = doc_ref[1].id
        default_channel_config = {
            "company_id": company_id,
            "instagram_post_count": 1,
            "facebook_post_count": 1,
            "linkedin_post_count": 1,
            "email_campaign_count": 1,
            "blog_post_count": 1,

            "instagram_active": True,
            "facebook_active": True,
            "linkedin_active": True,
            "email_campaign_active": True,
            "blog_post_active": True,

            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP
        }
        channel_config_doc_ref = db.collection("channel_config").document(company_id)
        channel_config_doc_ref.set(default_channel_config, merge=True)
        logger.info(f"✅ Channel config created successfully for company {company_id} : {doc_ref[1].id}")

        return {
            "status": "success",
            "message": f"✅ Company '{company.company_name}' created successfully",
            "id": company_id,
            "company_name": company.company_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating company '{company.company_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating company: {str(e)}")


@router.get("/company/{company_id}")
async def get_company(company_id: str, db: firestore.Client = Depends(get_db)):
    try:
        # Try to get from cache first
        cached_data = await redis_get(f"company_{company_id}")
        if cached_data:
            try:
                company_data = cached_data
                logger.info(f"✅ Cache hit for {company_id}")
                return company_data
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse cached data for {company_id}, fetching from DB")
        
        logger.info(f"❌ Cache miss for {company_id}")
        doc_ref = db.collection("companies").document(company_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail=f"Company {company_id} not found")

        company_data = doc.to_dict()
        company_data['company_id'] = company_id
        logger.info(f"Company '{company_id}' fetched successfully")

        # Convert Firestore datetime objects to ISO strings for JSON serialization
        company_data_serialized = convert_firestore_datetimes(company_data)

        # Save company data to redis (with fallback - continue even if cache fails)
        if await redis_set(f"company_{company_id}", json_dumps_firestore(company_data_serialized), ttl=604800): # 7 days in seconds
            logger.info(f"✅ Company '{company_id}' saved to redis successfully")
        else:
            logger.warning(f"⚠️ Failed to save company '{company_id}' to redis, continuing anyway")

        return company_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching company '{company_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching company: {str(e)}")


############################################# update company ###########################################

@router.put("/company/{company_id}")
async def update_company(company_id: str, company: CompanyRequest, db: firestore.Client = Depends(get_db)):
    try:
        # Invalidate cache before update
        if await redis_delete(f"company_{company_id}"):
            logger.info(f"✅ Company '{company_id}' removed from redis successfully")

        doc_ref = db.collection("companies").document(company_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail=f"Company {company_id} not found")

        update_data = company.model_dump(exclude_unset=True)

        # Convert None fields to empty arrays if applicable
        list_fields = [
            "fonts_typography", "keywords", "theme_colors",
            "products", "product_categories", "tone_analysis",
            "target_group", "industry", "composition_and_style",
            "environment_settings", "image_types_and_animation",
            "keywords_for_ai_image_generation", "lighting_and_color_tone",
            "subjects_and_people", "technology_elements", "theme_and_atmosphere",
            "company_name", "url", "company_info", "address",
            "favicon_url", "logo_url", "matched_fonts"
        ]
        for field in list_fields:
            if field in update_data and update_data[field] is None:
                # Access model_fields from the class, not the instance (Pydantic V3 requirement)
                field_info = CompanyRequest.model_fields.get(field)
                if field_info:
                    # Check if the annotation is a List type (handles Optional[List[...]] and List[...])
                    from typing import get_origin, get_args
                    annotation = field_info.annotation
                    origin = get_origin(annotation)
                    # Check if it's directly a list, or if it's a Union/Optional containing a list
                    is_list_type = (
                        origin is list or 
                        annotation is list or
                        (origin is not None and any(get_origin(arg) is list for arg in get_args(annotation)))
                    )
                    update_data[field] = [] if is_list_type else ""
                else:
                    # Fallback: default to empty string if field info not found
                    update_data[field] = ""

        update_data["updated_at"] = firestore.SERVER_TIMESTAMP

        if update_data:
            doc_ref.update(update_data)
            
            # Fetch updated company data to cache the complete record
            updated_doc = doc_ref.get()
            if updated_doc.exists:
                full_company_data = updated_doc.to_dict()
                full_company_data['company_id'] = company_id
                
                # Convert Firestore datetime objects to ISO strings for JSON serialization
                full_company_data_serialized = convert_firestore_datetimes(full_company_data)
                
                # Save full company data to redis (with fallback)
                if await redis_set(f"company_{company_id}", json_dumps_firestore(full_company_data_serialized), ttl=604800): # 7 days in seconds
                    logger.info(f"✅ Company '{company_id}' saved to redis successfully")
                else:
                    logger.warning(f"⚠️ Failed to save company '{company_id}' to redis, continuing anyway")

            # Run theme regeneration in background
            response_content =  await generate_all_themes_route(company_id, db)
            if response_content:
                logger.info(f"[Background] Themes generated successfully for {company_id}")
            else:
                logger.warning(f"[Background] No response from theme generator for {company_id}")

            return {
                "status": "success",
                "message": f"Company {company_id} updated successfully.",
                "updated_fields": list(update_data.keys())
            }
        
        logger.info(f"Company '{company_id}' updated successfully: {update_data}")
        return {"status": "success", "message": "No fields to update"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating company '{company_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating company: {str(e)}")


@router.delete("/company/{company_id}")
async def delete_company(company_id: str, db: firestore.Client = Depends(get_db)):
    try:
        # Remove from redis
        if await redis_delete(f"company_{company_id}"):
            logger.info(f"✅ Company '{company_id}' removed from redis successfully")

        doc_ref = db.collection("companies").document(company_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
        
        # delete all posts for the company
        facebook_posts = db.collection("facebook_posts").document(company_id).collection("posts").get()
        if facebook_posts:
            for post in facebook_posts:
                post.reference.delete()
        linkedin_posts = db.collection("linkedin_posts").document(company_id).collection("posts").get()
        if linkedin_posts:
            for post in linkedin_posts:
                post.reference.delete()
        instagram_posts = db.collection("instagram_posts").document(company_id).collection("posts").get()
        if instagram_posts:
            for post in instagram_posts:
                post.reference.delete()

       #delete themes for the company
        themes = db.collection("themes").document(company_id).collection("months").get()
        if themes:
            for month in themes:
                month.reference.delete()

        doc_ref.delete()
        logger.info(f"Company '{company_id}' deleted successfully")
        return {"status": "success", "message": f"Company {company_id} deleted"}
    except Exception as e:
        logger.error(f"Error deleting company '{company_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting company: {str(e)}")



############################################# get usage for a company ###########################################

@router.post("/compan/usage")
async def get_usage(request: UsageRequest, db: firestore.Client = Depends(get_db)):
    try:
        if not request.company_id or not request.year or not request.month:
            raise HTTPException(status_code=400, detail="Company ID, year, and month are required")
        usage_ref = db.collection("usage").document(request.company_id).collection(request.year).document(request.month).get()
        if not usage_ref.exists:
            raise HTTPException(status_code=404, detail=f"Usage not found for company {request.company_id} in {request.year} {request.month}")
        usage_data = usage_ref.to_dict()
        return usage_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting usage for {request.company_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting usage: {str(e)}")