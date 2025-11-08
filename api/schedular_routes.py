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
        post_data = {
            "theme":schedular.theme,
            "theme_description": schedular.theme_description,
            "instagram_post_count": schedular.instagram_post_count,
            "facebook_post_count": schedular.facebook_post_count,
            "linkedin_post_count": schedular.linkedin_post_count}

        scheduled_datetime = datetime.fromisoformat(schedular.scheduled_date.replace('Z', '+00:00'))

        final_data = {
            "post_data" : post_data,
            "scheduled_date": schedular.scheduled_date,
            "scheduled_at": scheduled_datetime,
            "status": "pending",
            "company_id": company_id,
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
        raise HTTPException(status_code=500, detail=f"  Coudn't schedule post for {company_data.get("name")} on {schedular.scheduled_date}")
    

@router.get("/schedule/{company_id}")
def get_all_scheduled_posts(company_id: str):
    try:
        schedular_ref = db.collection("scheduled_posts").document(company_id).collection("posts")
        schedular_data = list(schedular_ref.stream())

        if not schedular_data:
            raise HTTPException(status_code=400, detail=f"  Coudn't find schduled posts for company : {company_id}")
        
        response_data = []
        for doc in schedular_data:
            post_data = doc.to_dict()
            post_data["id"] = doc.id
            response_data.append(post_data)
        
        return {
            "status": "success",
            "count": len(response_data),
            "data": response_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"  coudn't get scheduled posts for {company_id}")
    

@router.get("/schedular/{company_id}/{month_id}")
def get_all_scheduled_posts_for_month(company_id: str, month_id: str):
    try:

        try:
            month_id = int(month_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Month ID must be a number (1-12)")

        # check month validity
        if month_id > 12 or month_id < 1:
            raise HTTPException(status_code=500, detail=f"  Requesting for Invalid month !!")
        
        
        # collect all posts
        posts_ref = db.collection("scheduled_posts").document(company_id).collection("posts")
        posts = posts_ref.stream()

        data = []

        # filter posts for specific month
        for doc in posts:
            post = doc.to_dict()
            scheduled_date = post.get('scheduled_date')
            if not scheduled_date:
                continue

            scheduled_date = scheduled_date.replace("Z", "+00:00")
            dt = datetime.fromisoformat(scheduled_date)
            month = dt.month 

            if month == month_id:
                data.append({
                    "id": doc.id,
                    **post
                })

        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"No scheduled posts for company '{company_id}' in month {month_id}"
            )

        return{
            "status": "success",
            "count": len(data),
            "data": data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"   no scheduled posts for month {month_id} of company {company_id}")
    



############################################# debug route #########################################################
# Add to content_routes.py or create a new debug route
@router.get("/debug/scheduled-posts/{company_id}")
def debug_scheduled_posts(company_id: str):
    try:
        db = get_firestore_client()
        
        # Check scheduled_posts collection
        scheduled_ref = db.collection("scheduled_posts").document(company_id).collection("posts")
        scheduled_docs = list(scheduled_ref.stream())
        
        scheduled_data = []
        for doc in scheduled_docs:
            data = doc.to_dict()
            scheduled_data.append({
                "id": doc.id,
                "data": data
            })
        
        return {
            "scheduled_posts": scheduled_data,
            "count": len(scheduled_data)
        }
    except Exception as e:
        return {"error": str(e)}




@router.post("/content/schedule/test-execute/{company_id}/{post_id}")
async def test_execute_scheduled_post(company_id: str, post_id: str):
    """Test route to force execute a specific scheduled post"""
    try:
        db = get_firestore_client()
        
        # Get the specific post
        post_ref = db.collection("scheduled_posts").document(company_id).collection("posts").document(post_id)
        post_doc = post_ref.get()
        
        if not post_doc.exists:
            raise HTTPException(status_code=404, detail="Post not found")
        
        data = post_doc.to_dict()
        
        logger.info(f"Force executing post {post_id} for company {company_id}")
        
        # Update status to processing
        post_ref.update({
            "status": "processing",
            "updated_at": firestore.SERVER_TIMESTAMP,
        })
        
        # Prepare data for content service
        post_data_for_content = {
            **data.get("post_data", {}),
            "scheduled_time": data.get("scheduled_date"),
            "company_id": company_id
        }
        
        from services.content_service import generate_scheduled_posts
        # Generate posts
        response = await generate_scheduled_posts(company_id, post_data_for_content)
        
        # Update status to completed
        post_ref.update({
            "status": "completed",
            "completed_at": firestore.SERVER_TIMESTAMP,
            "generated_post_ids": response.get("post_ids", [])
        })
        
        return {
            "status": "success",
            "message": f"Successfully executed post {post_id}",
            "generated_posts": response
        }
        
    except Exception as e:
        logger.error(f"Error in test execution: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Test execution failed: {str(e)}")