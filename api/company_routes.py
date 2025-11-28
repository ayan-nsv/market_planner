from fastapi import APIRouter, HTTPException
from google.cloud import firestore
from models.company_model import CompanyRequest

from fastapi import Depends
from config.firebase_config import get_firestore_client

from api.theme_routes import  generate_all_themes_route
from utils.logger import setup_logger


logger = setup_logger("marketing-app")

async def get_db():
    return get_firestore_client()


router = APIRouter()


@router.get("/company")
def get_companies(db: firestore.Client = Depends(get_db), page: int = 1, limit: int = 5):
    try:
        companies_ref = db.collection("companies")
        docs = companies_ref.limit(limit).offset((page-1)*limit).stream()
        companies = [{**doc.to_dict(), "id": doc.id} for doc in docs]
        logger.info(f"Companies fetched successfully: {companies}")
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

            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP    
        }
        doc_ref = db.collection("companies").add(company_data)
        logger.info(f"Company '{company.company_name}' created successfully: {doc_ref[1].id}")
        return {
            "status": "success",
            "message": f"Company '{company.company_name}' created successfully",
            "id": doc_ref[1].id,
            "company_name": company.company_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating company '{company.company_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating company: {str(e)}")


@router.get("/company/{company_id}")
def get_company(company_id: str, db: firestore.Client = Depends(get_db)):
    try:
        doc_ref = db.collection("companies").document(company_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail=f"Company {company_id} not found")

        company_data = doc.to_dict()
        company_data['company_id'] = company_id
        logger.info(f"Company '{company_id}' fetched successfully: {company_data}")
        return company_data
    except Exception as e:
        logger.error(f"Error fetching company '{company_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching company: {str(e)}")


############################################# update company ###########################################

@router.put("/company/{company_id}")
async def update_company(company_id: str, company: CompanyRequest, db: firestore.Client = Depends(get_db)):
    try:

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
def delete_company(company_id: str, db: firestore.Client = Depends(get_db)):
    try:
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
