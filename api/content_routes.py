from fastapi import APIRouter, HTTPException
from controllers.company_controller import create_company_image
from models.content_model import ContentRequest,ContentSaveRequest
from google.cloud import firestore
from datetime import datetime, timezone
from utils.logger import setup_logger

from config.firebase_config import get_firestore_client


from api.planner_routes import (generate_instagram_planner, 
                                generate_facebook_planner, 
                                generate_linkedin_planner)

logger = setup_logger("marketing-app")

router = APIRouter()



## generate posts for instagram
@router.post("/content/{company_id}/generate/instagram")
async def generate_image_instagram(content: ContentRequest, company_id: str):
    try:
        planner_info={
            "image_prompt" : content.image_prompt,
            "company_id": company_id,
            "channel" : "instagram"
        }
        result = await create_company_image(planner_info)
        
        logger.info(f"Content generation successful: {result}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating image: {str(e)}")



## generate posts for facebook
@router.post("/content/{company_id}/generate/facebook")
async def generate_image_facebook(content: ContentRequest, company_id: str):
    try:
        planner_info={
            "image_prompt" : content.image_prompt,
            "company_id": company_id,
            "channel" : "facebook"
        }
        result = await create_company_image(planner_info)
        
        logger.info(f"Content generation successful: {result}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating image: {str(e)}")




## generate posts for linkedin
@router.post("/content/{company_id}/generate/linkedin")
async def generate_image_linkedin(content: ContentRequest, company_id: str):
    try:
        planner_info={
            "image_prompt" : content.image_prompt,
            "company_id": company_id,
            "channel" : "linkedin"
        }
        result = await create_company_image(planner_info)
        
        logger.info(f"Content generation successful: {result}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating image: {str(e)}")


############################################### post save route ######################################################
@router.post("/content/{company_id}/instagram/save")
async def save_instagram_post_to_db(company_id: str, content: ContentSaveRequest):
    try:
        db = get_firestore_client()
        
        # Create the document data
        final_data = {
            "company_id": company_id,
            "channel": "instagram", 
            "image_url": content.image_url,
            "caption": content.caption,
            "hashtags": content.hashtags,
            "scheduled_time": content.scheduled_time,
            "scheduled_datetime": content.scheduled_datetime,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

        # Set the document data
        doc_ref = db.collection('instagram_posts').document(company_id).collection('posts').add(final_data)

        return {
            "status": "success",
            "company_id": company_id,
            "post_id": doc_ref[1].id,
            "scheduled_for": content.scheduled_time
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Post couldn't be saved: {str(e)}")


@router.post("/content/{company_id}/facebook/save")
async def save_facebook_post_to_db(company_id: str, content: ContentSaveRequest):
    try:
        db = get_firestore_client()
        
        # Create the document data
        final_data = {
            "company_id": company_id,
            "channel": "facebook", 
            "image_url": content.image_url,
            "caption": content.caption,
            "hashtags": content.hashtags,
            "scheduled_time": content.scheduled_time,
            "scheduled_datetime": content.scheduled_datetime,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

    
        # Set the document data
        doc_ref = db.collection('facebook_posts').document(company_id).collection('posts').add(final_data)

        return {
            "status": "success",
            "company_id": company_id,
            "post_id": doc_ref[1].id,
            "scheduled_for": content.scheduled_time
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Post couldn't be saved: {str(e)}")


@router.post("/content/{company_id}/linkedin/save")
async def save_linkedin_post_to_db(company_id: str, content: ContentSaveRequest):
    try:
        db = get_firestore_client()
        
        # Create the document data
        final_data = {
            "company_id": company_id,
            "channel": "linkedin", 
            "image_url": content.image_url,
            "caption": content.caption,
            "hashtags": content.hashtags,
            "scheduled_time": content.scheduled_time,
            "scheduled_datetime": content.scheduled_datetime,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        # Set the document data
        doc_ref = db.collection('linkedin_posts').document(company_id).collection('posts').add(final_data)

        return {
            "status": "success",
            "company_id": company_id,
            "post_id": doc_ref[1].id,
            "scheduled_for": content.scheduled_time
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Post couldn't be saved: {str(e)}")
                                                                                                                                                                                                                                                                                                                                                                                                                                                                       
#####################################################################################################


###################################################### Get posts ###################################################

@router.get("/content/{company_id}/instagram/post/{post_id}")
def get_instagram_post(company_id: str, post_id: str):
    try:
        db = get_firestore_client()
        post_ref = db.collection("instagram_posts").document(company_id).collection("posts").document(post_id)
        post_doc = post_ref.get()

        if post_doc.exists:
            post_data = post_doc.to_dict()
            post_data["post_id"] = post_doc.id  
            return {
                "status": "success",
                "data": post_data
            }
        else:
            raise HTTPException(status_code=404, detail=f"Post ID {post_id} not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Post: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching Post: {str(e)}")

@router.get("/content/{company_id}/facebook/post/{post_id}")
def get_facebook_post(company_id: str, post_id: str):
    try:
        db = get_firestore_client()
        post_ref = db.collection("facebook_posts").document(company_id).collection("posts").document(post_id)
        post_doc = post_ref.get()

        if post_doc.exists:
            post_data = post_doc.to_dict()
            post_data["post_id"] = post_doc.id  
            return {
                "status": "success",
                "data": post_data
            }
        else:
            raise HTTPException(status_code=404, detail=f"Post ID {post_id} not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Post: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching Post: {str(e)}")


@router.get("/content/{company_id}/linkedin/post/{post_id}")
def get_linkedin_post(company_id: str, post_id: str):
    try:
        db = get_firestore_client()
        post_ref = db.collection("linkedin_posts").document(company_id).collection("posts").document(post_id)
        post_doc = post_ref.get()

        if post_doc.exists:
            post_data = post_doc.to_dict()
            post_data["post_id"] = post_doc.id  
            return {
                "status": "success",
                "data": post_data
            }
        else:
            raise HTTPException(status_code=404, detail=f"Post ID {post_id} not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Post: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching Post: {str(e)}")

# #########################################################################################################################


@router.get("/content/{company_id}/instagram/posts")
def get_all_instagram_posts(company_id: str):
    try:
        db = get_firestore_client()
        posts_ref = db.collection("instagram_posts").document(company_id).collection("posts")
        
        posts = posts_ref.stream()
        
        posts_data = []
        for post in posts:
            post_data = post.to_dict()
            post_data["post_id"] = post.id
            posts_data.append(post_data)
        
        if posts_data:
            return {
                "data": posts_data
            }
        else:
            return {
                "data": [],
                "message": f"No posts found for company {company_id}"
            }

    except Exception as e:
        logger.error(f"Couldn't fetch the posts for {company_id}: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to fetch posts: {str(e)}"
        }
    

@router.get("/content/{company_id}/facebook/posts")
def get_all_facebook_posts(company_id: str):
    try:
        db = get_firestore_client()
        posts_ref = db.collection("facebook_posts").document(company_id).collection("posts")
        
        posts = posts_ref.stream()
        
        posts_data = []
        for post in posts:
            post_data = post.to_dict()
            post_data["post_id"] = post.id
            posts_data.append(post_data)
        
        if posts_data:
            return {
                "data": posts_data
            }
        else:
            return {
                "data": [],
                "message": f"No posts found for company {company_id}"
            }

    except Exception as e:
        logger.error(f"Couldn't fetch the posts for {company_id}: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to fetch posts: {str(e)}"
        }
    
@router.get("/content/{company_id}/linkedin/posts")
def get_all_linkedin_posts(company_id: str):
    try:
        db = get_firestore_client()
        posts_ref = db.collection("linkedin_posts").document(company_id).collection("posts")
        
        posts = posts_ref.stream()
        
        posts_data = []
        for post in posts:
            post_data = post.to_dict()
            post_data["post_id"] = post.id
            posts_data.append(post_data)
        
        if posts_data:
            return {
                "data": posts_data
            }
        else:
            return {
                "data": [],
                "message": f"No posts found for company {company_id}"
            }

    except Exception as e:
        logger.error(f"Couldn't fetch the posts for {company_id}: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to fetch posts: {str(e)}"
        }
###################################################  ############################################################



############################################# update post ###########################################
@router.put("/content/{company_id}/instagram/posts/{post_id}")
def update_instagram_post(company_id: str, post_id: str, content: ContentSaveRequest):
    try:
        db = get_firestore_client()
        
        # Correct document reference - point to the specific post document
        doc_ref = db.collection("instagram_posts").document(company_id).collection("posts").document(post_id)
        
        doc_snapshot = doc_ref.get()
        if not doc_snapshot.exists:
            raise HTTPException(status_code=404, detail=f"Post {post_id} not found for company {company_id}")
        
        # Prepare update data
        update_data = content.model_dump(exclude_unset=True)
        
        for field in ['caption', 'hashtags', 'scheduled_time', 'image_url']:
            if field in update_data and update_data[field] is None:
                update_data[field] = []
        
        update_data["updated_at"] = firestore.SERVER_TIMESTAMP
        
        if update_data:
            doc_ref.update(update_data)
            return {
                "status": "success", 
                "message": f"Post {post_id} for Company {company_id} updated",
                "updated_fields": list(update_data.keys())
            }
        else:
            return {"status": "success", "message": "No fields to update"}
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating post: {str(e)}")




@router.put("/content/{company_id}/facebook/posts/{post_id}")
def update_facebook_post(company_id: str, post_id: str, content: ContentSaveRequest):
    try:
        db = get_firestore_client()
        
        # Correct document reference - point to the specific post document
        doc_ref = db.collection("facebook_posts").document(company_id).collection("posts").document(post_id)
        
        doc_snapshot = doc_ref.get()
        if not doc_snapshot.exists:
            raise HTTPException(status_code=404, detail=f"Post {post_id} not found for company {company_id}")
        
        # Prepare update data
        update_data = content.model_dump(exclude_unset=True)
        
        for field in ['caption', 'hashtags', 'scheduled_time', 'image_url']:
            if field in update_data and update_data[field] is None:
                update_data[field] = []
        
        update_data["updated_at"] = firestore.SERVER_TIMESTAMP
        
        if update_data:
            doc_ref.update(update_data)
            return {
                "status": "success", 
                "message": f"Post {post_id} for Company {company_id} updated",
                "updated_fields": list(update_data.keys())
            }
        else:
            return {"status": "success", "message": "No fields to update"}
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating post: {str(e)}")
    


@router.put("/content/{company_id}/linkedin/posts/{post_id}")
def update_linkedin_post(company_id: str, post_id: str, content: ContentSaveRequest):
    try:
        db = get_firestore_client()
        
        # Correct document reference - point to the specific post document
        doc_ref = db.collection("linkedin_posts").document(company_id).collection("posts").document(post_id)
        
        doc_snapshot = doc_ref.get()
        if not doc_snapshot.exists:
            raise HTTPException(status_code=404, detail=f"Post {post_id} not found for company {company_id}")
        
        # Prepare update data
        update_data = content.model_dump(exclude_unset=True)
        
        for field in ['caption', 'hashtags', 'scheduled_time', 'image_url']:
            if field in update_data and update_data[field] is None:
                update_data[field] = []
        
        update_data["updated_at"] = firestore.SERVER_TIMESTAMP
        
        if update_data:
            doc_ref.update(update_data)
            return {
                "status": "success", 
                "message": f"Post {post_id} for Company {company_id} updated",
                "updated_fields": list(update_data.keys())
            }
        else:
            return {"status": "success", "message": "No fields to update"}
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating post: {str(e)}")

#########################################################################################################

################################# generate and save posts to db (automation) ############################
from services.scheduler_service import process_due_posts
@router.post("/content/schedule/execute", tags=["Trigger Scheduler"])
async def execute_scheduled_posts():
      return await process_due_posts()
