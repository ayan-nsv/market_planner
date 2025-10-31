from fastapi import APIRouter, HTTPException
from google.cloud import firestore
from models.company_model import CompanyRequest
from typing import List
from config.firebase_config import get_firestore_client


router = APIRouter()

@router.get("/company")
def get_companies():
    try:
        db = get_firestore_client()
        companies_ref = db.collection("companies")
        docs = companies_ref.stream()
        companies = [{**doc.to_dict(), "id": doc.id} for doc in docs]
        return companies
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching companies: {str(e)}")


@router.post("/company")
async def create_company(company: CompanyRequest):
    try:
        db = get_firestore_client()
        
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
            "company_name": company.company_name,
            "company_url": company.company_url or "",
            "company_info": company.company_info or "",
            "address": company.address or "",
            "favicon_url": company.favicon_url or "",
            "font_typography": company.font_typography or [],
            "industry": company.industry or "",
            "keywords": company.keywords or [],
            "logo_url": company.logo_url or "",
            "target_group": company.target_group or "",
            "theme_colors": company.theme_colors or [],
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP
        }
        doc_ref = db.collection("companies").add(company_data)
        
        return {
            "status": "success",
            "message": f"Company '{company.company_name}' created successfully",
            "id": doc_ref[1].id,
            "company_name": company.company_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating company: {str(e)}")



@router.get("/company/{company_id}")
def get_company(company_id: str):
    try:
        db = get_firestore_client()
        doc_ref = db.collection("companies").document(company_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail=f"Company {company_id} not found")

        company_data = doc.to_dict()
        company_data['company_id'] = company_id
        
        return company_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching company: {str(e)}")


@router.put("/company/{company_id}")
def update_company(company_id: str, company: CompanyRequest):
    try:
        db = get_firestore_client()
        doc_ref = db.collection("companies").document(company_id)
        
        if not doc_ref.get().exists:
            raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
        
        update_data = company.model_dump(exclude_unset=True)
        
        for field in ['font_typography', 'keywords', 'theme_colors']:
            if field in update_data and update_data[field] is None:
                update_data[field] = []
        
        update_data["updated_at"] = firestore.SERVER_TIMESTAMP
        
        if update_data:
            doc_ref.update(update_data)
            return {
                "status": "success", 
                "message": f"Company {company_id} updated",
                "updated_fields": list(update_data.keys())
            }
        else:
            return {"status": "success", "message": "No fields to update"}
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating company: {str(e)}")




@router.delete("/company/{company_id}")
def delete_company(company_id: str):
    try:
        db = get_firestore_client()
        doc_ref = db.collection("companies").document(company_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
        doc_ref.delete()
        return {"status": "success", "message": f"Company {company_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting company: {str(e)}")
