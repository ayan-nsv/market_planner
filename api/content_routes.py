from fastapi import Depends
from fastapi import APIRouter, HTTPException

from models.content_model import ContentRequest,ContentSaveRequest
from models.schedular_model import SchedularRequest
from models.content_model import ReframeImageRequest

from services.gemini_service import generate_reformatted_image
from services.firebase_service import upload_image

from controllers.company_controller import create_company_image

from google.cloud import firestore
from datetime import datetime, timezone
from utils.logger import setup_logger

from config.firebase_config import get_firestore_client

from services.content_service import get_image_bytes


logger = setup_logger("marketing-app")


router = APIRouter()


async def get_db():
    return get_firestore_client()

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
async def save_instagram_post_to_db(company_id: str, content: ContentSaveRequest, db: firestore.Client = Depends(get_db)):
    try:
        
        
        # Create the document data
        final_data = {
            "company_id": company_id,
            "channel": "instagram", 
            "image_url": content.image_url,
            "caption": content.caption,
            "hashtags": content.hashtags,
            "scheduled_time": content.scheduled_time,
            "scheduled_datetime": content.scheduled_datetime,
            "status": "scheduled",

            "month_id": content.month_id,
            "theme_index": content.theme_index,


            "overlay_text": content.overlay_text,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        existing_posts = list(db.collection('instagram_posts').document(company_id).collection('posts').where("month_id", "==", content.month_id).where("theme_index", "==", content.theme_index).stream())
        variation_index = len(existing_posts)
        if variation_index > 0:
            variation_index = variation_index + 1
        else:
            variation_index = 1
        final_data["variation_index"] = variation_index

        # Set the document data
        doc_ref = db.collection('instagram_posts').document(company_id).collection('posts').add(final_data)
        logger.info(f"Instagram post saved successfully: {doc_ref[1].id}")
        return {
            "status": "scheduled",
            "company_id": company_id,
            "post_id": doc_ref[1].id,
            "scheduled_for": content.scheduled_time
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving Instagram post: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Post couldn't be saved: {str(e)}")


@router.post("/content/{company_id}/facebook/save")
async def save_facebook_post_to_db(company_id: str, content: ContentSaveRequest, db: firestore.Client = Depends(get_db)):
    try:
        
        # Create the document data
        final_data = {
            "company_id": company_id,
            "channel": "facebook", 
            "image_url": content.image_url,
            "caption": content.caption,
            "hashtags": content.hashtags,
            "scheduled_time": content.scheduled_time,
            "scheduled_datetime": content.scheduled_datetime,
            "status": "scheduled",

            "month_id": content.month_id,
            "theme_index": content.theme_index,

            "overlay_text": content.overlay_text,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        existing_posts = list(db.collection('facebook_posts').document(company_id).collection('posts').where("month_id", "==", content.month_id).where("theme_index", "==", content.theme_index).stream())
        variation_index = len(existing_posts)
        if variation_index > 0:
            variation_index = variation_index + 1
        else:
            variation_index = 1
        final_data["variation_index"] = variation_index
    
        # Set the document data
        doc_ref = db.collection('facebook_posts').document(company_id).collection('posts').add(final_data)
        logger.info(f"Facebook post saved successfully: {doc_ref[1].id}")
        return {
            "status": "scheduled",
            "company_id": company_id,
            "post_id": doc_ref[1].id,
            "scheduled_for": content.scheduled_time
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving Facebook post: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Post couldn't be saved: {str(e)}")


@router.post("/content/{company_id}/linkedin/save")
async def save_linkedin_post_to_db(company_id: str, content: ContentSaveRequest, db: firestore.Client = Depends(get_db)):
    try:
        # Create the document data
        final_data = {
            "company_id": company_id,
            "channel": "linkedin", 
            "image_url": content.image_url,
            "caption": content.caption,
            "hashtags": content.hashtags,
            "scheduled_time": content.scheduled_time,
            "scheduled_datetime": content.scheduled_datetime,
            "status": "scheduled",

            "month_id": content.month_id,
            "theme_index": content.theme_index,

            "overlay_text": content.overlay_text,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        existing_posts = list(db.collection('linkedin_posts').document(company_id).collection('posts').where("month_id", "==", content.month_id).where("theme_index", "==", content.theme_index).stream())
        variation_index = len(existing_posts)
        if variation_index > 0:
            variation_index = variation_index + 1
        else:
            variation_index = 1
        final_data["variation_index"] = variation_index
        
        # Set the document data
        doc_ref = db.collection('linkedin_posts').document(company_id).collection('posts').add(final_data)
        logger.info(f"LinkedIn post saved successfully: {doc_ref[1].id}")
        return {
            "status": "scheduled",
            "company_id": company_id,
            "post_id": doc_ref[1].id,
            "scheduled_for": content.scheduled_time
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving LinkedIn post: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Post couldn't be saved: {str(e)}")
                                                                                                                                                                                                                                                                                                                                                                                                                                                                       
#####################################################################################################


###################################################### Get posts ###################################################

@router.get("/content/{company_id}/instagram/post/{post_id}")
def get_instagram_post(company_id: str, post_id: str, db: firestore.Client = Depends(get_db)):
    try:
        
        post_ref = db.collection("instagram_posts").document(company_id).collection("posts").document(post_id)
        post_doc = post_ref.get()

        if post_doc.exists:
            post_data = post_doc.to_dict()
            post_data["post_id"] = post_doc.id  
            status = post_data["status"]
            logger.info(f"Instagram post '{post_id}' fetched successfully: {post_data}")
            return {
                "status": status,
                "data": post_data
            }
        else:
            raise HTTPException(status_code=404, detail=f"Post ID {post_id} not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Instagram post '{post_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching Instagram post: {str(e)}")

@router.get("/content/{company_id}/facebook/post/{post_id}")
def get_facebook_post(company_id: str, post_id: str, db: firestore.Client = Depends(get_db)):
    try:
        post_ref = db.collection("facebook_posts").document(company_id).collection("posts").document(post_id)
        post_doc = post_ref.get()

        if post_doc.exists:
            post_data = post_doc.to_dict()
            post_data["post_id"] = post_doc.id  
            status = post_data["status"]
            logger.info(f"Facebook post '{post_id}' fetched successfully: {post_data}")
            return {
                "status": status,
                "data": post_data
            }
        else:
            raise HTTPException(status_code=404, detail=f"Post ID {post_id} not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Facebook post '{post_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching Facebook post: {str(e)}")

@router.get("/content/{company_id}/linkedin/post/{post_id}")
def get_linkedin_post(company_id: str, post_id: str, db: firestore.Client = Depends(get_db)):
    try:
        post_ref = db.collection("linkedin_posts").document(company_id).collection("posts").document(post_id)
        post_doc = post_ref.get()

        if post_doc.exists:
            post_data = post_doc.to_dict()
            post_data["post_id"] = post_doc.id  
            status = post_data["status"]
            logger.info(f"LinkedIn post '{post_id}' fetched successfully: {post_data}")
            return {
                "status": status,
                "data": post_data
            }
        else:
            raise HTTPException(status_code=404, detail=f"Post ID {post_id} not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching LinkedIn post '{post_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching Post: {str(e)}")

# #########################################################################################################################

###################################################### get posts with variation and theme index ##################################################
@router.get("/content/{company_id}/variation/{theme_index}", tags=["post_variation"])
def get_social_media_posts_with_theme_index(company_id: str, month_id: int, channel: str, theme_index: int, db: firestore.Client = Depends(get_db)):
    try:
        channel = channel.lower().strip()   
        if channel not in ["instagram", "facebook", "linkedin"]:
            raise HTTPException(status_code=400, detail="Invalid channel")

        posts_ref = db.collection(f"{channel}_posts").document(company_id).collection("posts").where("month_id", "==", month_id).where("theme_index", "==", theme_index)
        posts = posts_ref.stream()
        posts_data = []
        for post in posts:
            post_data = post.to_dict()
            post_data["post_id"] = post.id
            posts_data.append(post_data)
        logger.info(f"Posts fetched successfully with variation and theme index: {posts_data}")
        return {
            "data": posts_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching posts with variation and theme index for company {company_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching posts with variation and theme index: {str(e)}")

###################################################################################################################################

@router.get("/content/{company_id}/instagram/posts")
def get_all_instagram_posts(company_id: str, db: firestore.Client = Depends(get_db)):
    try:
        posts_ref = db.collection("instagram_posts").document(company_id).collection("posts")
        
        posts = posts_ref.stream()
        
        posts_data = []
        for post in posts:
            post_data = post.to_dict()
            post_data["post_id"] = post.id
            posts_data.append(post_data)
        
        if posts_data:
            logger.info(f"All Instagram posts fetched successfully for company {company_id}: {posts_data}")
            return {
                "data": posts_data
            }
        else:
            logger.info(f"No Instagram posts found for company {company_id}")
            return {
                "data": [],
                "message": f"No posts found for company {company_id}"
            }

    except Exception as e:
        logger.error(f"Couldn't fetch the Instagram posts for company {company_id}: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to fetch posts: {str(e)}"
        }
    
@router.get("/content/{company_id}/facebook/posts")
def get_all_facebook_posts(company_id: str, db: firestore.Client = Depends(get_db)):
    try:
        posts_ref = db.collection("facebook_posts").document(company_id).collection("posts")
        
        posts = posts_ref.stream()
        
        posts_data = []
        for post in posts:
            post_data = post.to_dict()
            post_data["post_id"] = post.id
            posts_data.append(post_data)
        
        if posts_data:
            logger.info(f"All Facebook posts fetched successfully for company {company_id}: {posts_data}")
            return {
                "data": posts_data
            }
        else:
            logger.info(f"No Facebook posts found for company {company_id}")
            return {
                "data": [],
                "message": f"No posts found for company {company_id}"
            }

    except Exception as e:
        logger.error(f"Couldn't fetch the Facebook posts for company {company_id}: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to fetch posts: {str(e)}"
        }
    
@router.get("/content/{company_id}/linkedin/posts")
def get_all_linkedin_posts(company_id: str, db: firestore.Client = Depends(get_db)):
    try:
        posts_ref = db.collection("linkedin_posts").document(company_id).collection("posts")
        
        posts = posts_ref.stream()
        
        posts_data = []
        for post in posts:
            post_data = post.to_dict()
            post_data["post_id"] = post.id
            posts_data.append(post_data)
        
        if posts_data:
            logger.info(f"All LinkedIn posts fetched successfully for company {company_id}: {posts_data}")
            return {
                "data": posts_data
            }
        else:
            logger.info(f"No LinkedIn posts found for company {company_id}")
            return {
                "data": [],
                "message": f"No posts found for company {company_id}"
            }

    except Exception as e:
        logger.error(f"Couldn't fetch the LinkedIn posts for company {company_id}: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to fetch posts: {str(e)}"
        }

#####################################################  ############################################################



############################################# update post ###########################################
@router.put("/content/{company_id}/instagram/posts/{post_id}")
def update_instagram_post(company_id: str, post_id: str, content: ContentSaveRequest, db: firestore.Client = Depends(get_db)):
    try:
        
        # Correct document reference - point to the specific post document
        doc_ref = db.collection("instagram_posts").document(company_id).collection("posts").document(post_id)
        
        doc_snapshot = doc_ref.get()
        if not doc_snapshot.exists:
            raise HTTPException(status_code=404, detail=f"Post {post_id} not found for company {company_id}")
        
        # Prepare update data
        update_data = content.model_dump(exclude_unset=True)
        
        for field in ['caption', 'hashtags', 'scheduled_time', 'image_url', 'status']:
            if field in update_data and update_data[field] is None:
                update_data[field] = []
        if 'scheduled_time' in update_data:
            update_data["scheduled_datetime"] = datetime.fromisoformat(update_data["scheduled_time"].replace('Z', '+00:00'))
            update_data["status"] = "scheduled"

        update_data["updated_at"] = firestore.SERVER_TIMESTAMP
        
        if update_data:
            doc_ref.update(update_data)
            logger.info(f"Instagram post '{post_id}' updated successfully: {update_data}")
            return {
                "status": "scheduled", 
                "message": f"Post {post_id} for Company {company_id} updated",
                "updated_fields": list(update_data.keys())
            }
        else:
            return {"status": "success", "message": "No fields to update"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Instagram post '{post_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating post: {str(e)}")

@router.put("/content/{company_id}/facebook/posts/{post_id}")
def update_facebook_post(company_id: str, post_id: str, content: ContentSaveRequest, db: firestore.Client = Depends(get_db)):
    try:
        
        # Correct document reference - point to the specific post document
        doc_ref = db.collection("facebook_posts").document(company_id).collection("posts").document(post_id)
        
        doc_snapshot = doc_ref.get()
        if not doc_snapshot.exists:
            raise HTTPException(status_code=404, detail=f"Post {post_id} not found for company {company_id}")
        
        # Prepare update data
        update_data = content.model_dump(exclude_unset=True)
        
        for field in ['caption', 'hashtags', 'scheduled_time', 'image_url', 'status']:
            if field in update_data and update_data[field] is None:
                update_data[field] = []
        if 'scheduled_time' in update_data:
            update_data["scheduled_datetime"] = datetime.fromisoformat(update_data["scheduled_time"].replace('Z', '+00:00'))
            update_data["status"] = "scheduled"
        
        update_data["updated_at"] = firestore.SERVER_TIMESTAMP
        
        if update_data:
            doc_ref.update(update_data)
            logger.info(f"Facebook post '{post_id}' updated successfully: {update_data}")
            return {
                "status": "scheduled", 
                "message": f"Post {post_id} for Company {company_id} updated",
                "updated_fields": list(update_data.keys())
            }
        else:
            return {"status": "scheduled", "message": "No fields to update"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Facebook post '{post_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating post: {str(e)}")
    
@router.put("/content/{company_id}/linkedin/posts/{post_id}")
def update_linkedin_post(company_id: str, post_id: str, content: ContentSaveRequest, db: firestore.Client = Depends(get_db)):
    try:

        # Correct document reference - point to the specific post document
        doc_ref = db.collection("linkedin_posts").document(company_id).collection("posts").document(post_id)
        
        doc_snapshot = doc_ref.get()
        if not doc_snapshot.exists:
            raise HTTPException(status_code=404, detail=f"Post {post_id} not found for company {company_id}")
        
        # Prepare update data
        update_data = content.model_dump(exclude_unset=True)
        
        for field in ['caption', 'hashtags', 'scheduled_time', 'image_url', 'status']:
            if field in update_data and update_data[field] is None:
                update_data[field] = []
        if 'scheduled_time' in update_data:
            update_data["scheduled_datetime"] = datetime.fromisoformat(update_data["scheduled_time"].replace('Z', '+00:00'))
            update_data["status"] = "scheduled"
        
        update_data["updated_at"] = firestore.SERVER_TIMESTAMP
        
        if update_data:
            doc_ref.update(update_data)
            logger.info(f"LinkedIn post '{post_id}' updated successfully: {update_data}")
            return {
                "status": "scheduled", 
                "message": f"Post {post_id} for Company {company_id} updated",
                "updated_fields": list(update_data.keys())
            }
        else:
            return {"status": "scheduled", "message": "No fields to update"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating LinkedIn post '{post_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating post: {str(e)}")

#########################################################################################################


@router.post("/content/{company_id}/schedule/create")
async def create_scheduled_posts(company_id: str, schedular_request: SchedularRequest, db: firestore.Client = Depends(get_db)):
    try:
        from services.content_service import generate_scheduled_posts
        response_content = await generate_scheduled_posts(company_id, schedular_request.model_dump(), db)
        logger.info(f"Scheduled posts created successfully for company {company_id}: {response_content}")
        return response_content
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating scheduled posts for company {company_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating scheduled posts: {str(e)}")



#################################################### reframing post (future) ##################################################

# Constants for image reformatting (defined at module level to avoid recreation)
VALID_RATIOS = ["1:1", "3:2", "2:3"]
VALID_CHANNELS = {"instagram", "facebook", "linkedin"}
MIME_TYPE_EXT_MAP = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
}
MIN_IMAGE_SIZE = 1024  

@router.post("/content/image/reformat")
async def reformat_post_image(image: ReframeImageRequest, db: firestore.Client = Depends(get_db)):
    """
    Reformat post image to a new aspect ratio.
    Optimized for memory and CPU efficiency.
    """
    try:
        # Early validation to fail fast
        if image.target_ratio < 0 or image.target_ratio >= len(VALID_RATIOS):
            logger.error(f"Invalid target_ratio for post {image.post_id} for company {image.company_id}: {image.target_ratio}")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid target_ratio. Must be 0-{len(VALID_RATIOS)-1}"
            )

        channel = image.channel.lower().strip()
        if channel not in VALID_CHANNELS:
            logger.error(f"Invalid channel for post {image.post_id} for company {image.company_id}: {channel}")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid channel. Must be one of: {', '.join(VALID_CHANNELS)}"
            )

        # Optimize Firestore query: only fetch the image_url field instead of entire document
        doc_ref = (
            db.collection(f"{channel}_posts")
            .document(image.company_id)
            .collection("posts")
            .document(image.post_id)
        )
        doc_snapshot = doc_ref.get()
        
        if not doc_snapshot.exists:
            logger.error(f"Post {image.post_id} not found for company {image.company_id}")
            raise HTTPException(
                status_code=404, 
                detail=f"Post {image.post_id} not found for company {image.company_id}"
            )
        
        # Get only the image_url field (more efficient than fetching entire document)
        doc_data = doc_snapshot.to_dict()
        image_url = doc_data.get("image_url") if doc_data else None
        
        if not image_url:
            logger.error(f"Post {image.post_id} has no image URL for company {image.company_id}")
            raise HTTPException(status_code=400, detail="Post has no image URL")

        # Download and convert image to base64 bytes (required by Gemini API)
        image_bytes_base64 = await get_image_bytes(image_url)
        
        # Get target ratio from constant array
        target_ratio = VALID_RATIOS[image.target_ratio]
        
        # Generate reformatted image (with automatic retry for rate limits)
        reformatted_result = await generate_reformatted_image(image_bytes_base64, target_ratio)
        
        if not reformatted_result:
            logger.error(f"Failed to generate reformatted image for post {image.post_id} for company {image.company_id}")
            raise HTTPException(
                status_code=503,  # Service Unavailable - more appropriate for rate limits/API failures
                detail="Failed to generate reformatted image. This may be due to API rate limits. Please try again in a few moments."
            )
        
        reformatted_image_bytes, mime_type = reformatted_result

        # Validate reformatted image size
        if not reformatted_image_bytes or len(reformatted_image_bytes) < MIN_IMAGE_SIZE:
            logger.error(f"Generated image appears invalid or truncated for post {image.post_id} for company {image.company_id}")
            raise HTTPException(
                status_code=500, 
                detail="Generated image appears invalid or truncated"
            )

        # Determine file extension from mime type
        file_ext = MIME_TYPE_EXT_MAP.get(mime_type, ".png")
        path = f"content/{image.company_id}/{image.post_id}{file_ext}"

        # Upload reformatted image
        reformatted_image_url = await upload_image(
            reformatted_image_bytes, 
            path, 
            content_type=mime_type
        )

        # Clear large objects from memory (Python GC will handle this, but explicit deletion helps)
        del image_bytes_base64, reformatted_image_bytes, reformatted_result
        # Note: gc.collect() is removed as it's expensive and Python's GC handles this automatically

        # Update Firestore document with new image URL
        doc_ref.update({"image_url": reformatted_image_url})

        logger.info(f"Post image reformatted successfully for post {image.post_id} for company {image.company_id}: {reformatted_image_url}")
        return {
            "status": "success",
            "message": "Post image reformatted successfully",
            "reformatted_image_url": reformatted_image_url
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reframing post image for post {image.post_id} for company {image.company_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error reframing post image for post {image.post_id} for company {image.company_id}: {str(e)}"
        )










