from fastapi import APIRouter, HTTPException
from models.theme_model import ThemeRequest
from services.gpt_service import generate_all_themes, generate_theme

from google.cloud import firestore
from fastapi import Depends
from config.firebase_config import get_firestore_client

import json
from utils.logger import setup_logger

logger = setup_logger("marketing-app")

router = APIRouter()

async def get_db():
    return get_firestore_client()


def parse_themes_response(response_content: str):
    try:
        themes = json.loads(response_content)
        for month in themes:
            # Ensure "themes" key exists
            if "themes" not in month or not isinstance(month["themes"], list):
                month["themes"] = []
        return themes
    except json.JSONDecodeError:
        raise ValueError(f"Model did not return valid JSON: {response_content[:200]}")


def ensure_all_months(themes):

    expected_months = [
        "January","February","March","April","May","June",
        "July","August","September","October","November","December"
    ]
    normalized_themes = []
    for i, month_name in enumerate(expected_months, start=1):
        month_data = next((m for m in themes if m.get("month", "").lower() == month_name.lower()), None)
        if month_data:
            month_data["month_id"] = i
            normalized_themes.append(month_data)
        else:
            normalized_themes.append({"month": month_name, "month_id": i, "themes": []})
    return normalized_themes


# Get a single theme from a month
@router.get("/themes/{company_id}/{month_id}")
def get_theme(company_id: str, month_id: int, db: firestore.Client = Depends(get_db)):
    try:
        doc_ref = db.collection("themes").document(company_id).collection("months").document(str(month_id))
        doc = doc_ref.get()
        if not doc.exists:
            logger.error(f"Theme for month {month_id} not found")
            raise HTTPException(status_code=404, detail=f"Theme for month {month_id} not found")
        logger.info(f"Theme for month {month_id} fetched successfully: {doc.to_dict()}")
        return doc.to_dict()
    except Exception as e:
        logger.error(f"Error getting theme for month {month_id}: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Could not get theme for month {month_id}: {str(e)}")


@router.post("/themes/{company_id}/{month_id}/regenerate")
def regenerate_month_theme(company_id: str, month_id: int, db: firestore.Client = Depends(get_db)):
    try:
        # Validate month_id
        if month_id < 1 or month_id > 12:
            logger.error(f"Invalid month_id: {month_id}")
            raise HTTPException(status_code=400, detail="month_id must be between 0 and 11")
        
        company_ref = db.collection("companies").document(company_id)
        company_doc = company_ref.get()
        if not company_doc.exists:
            logger.error(f"Company {company_id} not found")
            raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
        company_data = company_doc.to_dict()

        list_of_months = {"1":"January", "2":"February", "3":"March", "4":"April", "5":"May", "6":"June", 
                         "7":"July", "8":"August", "9":"September", "10":"October", "11":"November", "12":"December"}

        month_name = list_of_months[str(month_id)]
        
        existing_themes = None
        month_ref = db.collection("themes").document(company_id).collection("months").document(str(month_id))
        existing_doc = month_ref.get()
        
        if existing_doc.exists:
            existing_themes = existing_doc.to_dict()
            logger.info(f"Found existing themes for {month_name}: {existing_themes.get('themes', [])}")

        theme_data = generate_theme(company_data, month_name, existing_themes)
        logger.info(f"Theme generated successfully for {month_name}: {theme_data.get('themes', [])}")
        month_data = {
            "month_id": month_id,
            "month": month_name,
            "themes": theme_data["themes"],
        }

        # Update Firestore
        month_ref.set(month_data, merge=True)
        logger.info(f"Theme updated successfully for {month_name}: {month_data.get('themes', [])}")
        return {
            "data": month_data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating theme for {month_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error regenerating theme: {str(e)}")


# Generate all themes for a company
@router.post("/themes/{company_id}/generate-all")
async def generate_all_themes_route(company_id: str, db: firestore.Client = Depends(get_db)):
    try:
        company_ref = db.collection("companies").document(company_id)
        company_doc = company_ref.get()
        if not company_doc.exists:
            logger.error(f"Company {company_id} not found")
            raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
        company_data = company_doc.to_dict()

        # Call GPT service
        response_content = await generate_all_themes(company_data)
        if isinstance(response_content, str):
            themes = parse_themes_response(response_content)
        elif isinstance(response_content, list):
            themes = response_content
        else:
            logger.error(f"Invalid GPT response: {type(response_content)}")
            raise HTTPException(status_code=500, detail=f"Invalid GPT response: {type(response_content)}")
        themes = ensure_all_months(themes)

        # Save to Firestore using numeric IDs
        months_ref = db.collection("themes").document(company_id).collection("months")
        for month in themes:
            month_id = month["month_id"]
            months_ref.document(str(month_id)).set(month)

        logger.info(f"All themes generated successfully for company {company_id}")
        return {"message": "All themes generated successfully"}

    except Exception as e:
        logger.error(f"Error generating themes for company {company_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating themes: {str(e)}")

@router.get("/themes/{company_id}")
def get_all_themes(company_id: str, db: firestore.Client = Depends(get_db)):
    try:
        months_ref = db.collection("themes").document(company_id).collection("months")
        month_docs = months_ref.stream() 

        data = []
        for doc in month_docs:
            item = doc.to_dict()
            item["month_id"] = doc.id 
            data.append(item)

        if not data:
            logger.error(f"No themes found for company {company_id}")
            raise HTTPException(status_code=404, detail="No themes found for this company")

        return {
            "status": "success",
            "count": len(data),
            "data": data
        }

    except Exception as e:
        logger.error(f"Error getting themes for company {company_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Could not get themes: {str(e)}")
