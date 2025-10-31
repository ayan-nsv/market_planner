from fastapi import APIRouter, HTTPException
from models.theme_model import ThemeRequest
from google.cloud import firestore
from services.gpt_service import generate_all_themes, generate_theme
import json

router = APIRouter()
db = firestore.Client()


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
def get_theme(company_id: str, month_id: int):
    try:
        doc_ref = db.collection("themes").document(company_id).collection("months").document(str(month_id))
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail=f"Theme for month {month_id} not found")
        return doc.to_dict()
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Could not get theme for month {month_id}: {str(e)}")


@router.post("/themes/{company_id}/{month_id}/regenerate")
def regenerate_month_theme(company_id: str, month_id: int):
    try:
        # Validate month_id
        if month_id < 1 or month_id > 12:
            raise HTTPException(status_code=400, detail="month_id must be between 0 and 11")
        
        company_ref = db.collection("companies").document(company_id)
        company_doc = company_ref.get()
        if not company_doc.exists:
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
            print(f"Found existing themes for {month_name}: {existing_themes.get('themes', [])}")

        theme_data = generate_theme(company_data, month_name, existing_themes)
        
        month_data = {
            "month_id": month_id,
            "month": month_name,
            "themes": theme_data["themes"],
        }

        # Update Firestore
        month_ref.set(month_data, merge=True)
        
        return {
            "data": month_data,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error regenerating theme: {str(e)}")


# Generate all themes for a company
@router.post("/themes/{company_id}/generate-all")
def generate_all_themes_route(company_id: str):
    try:
        company_ref = db.collection("companies").document(company_id)
        company_doc = company_ref.get()
        if not company_doc.exists:
            raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
        company_data = company_doc.to_dict()

        # Call GPT service
        response_content = generate_all_themes(company_data)
        if isinstance(response_content, str):
            themes = parse_themes_response(response_content)
        elif isinstance(response_content, list):
            themes = response_content
        else:
            raise HTTPException(status_code=500, detail=f"Invalid GPT response: {type(response_content)}")
        themes = ensure_all_months(themes)

        # Save to Firestore using numeric IDs
        months_ref = db.collection("themes").document(company_id).collection("months")
        for month in themes:
            month_id = month["month_id"]
            months_ref.document(str(month_id)).set(month)

        return {"message": "All themes generated successfully", "data": themes}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating themes: {str(e)}")





##### future updates #####

# Update a specific theme document under a month
# @router.put("/themes/{company_id}/{month_id}")
# def update_theme(company_id: str, month_id: int, theme: ThemeRequest):
#     try:
#         doc_ref = db.collection("themes").document(company_id).collection("months").document(str(month_id))
#         doc_ref.update(theme.model_dump())
#         return {"status": "success", "message": f"Theme {month_id} updated successfully"}

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error updating theme: {str(e)}")



# Delete a specific theme document under a month
# @router.delete("/themes/{company_id}/{month_id}")
# def delete_theme(company_id: str, month_id: int):
#     try:
#         doc_ref = db.collection("themes").document(company_id).collection("months").document(str(month_id))
#         doc_ref.delete()
#         return {"status": "success", "message": f"Theme {month_id} deleted successfully"}

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error deleting theme: {str(e)}")
