import json
from fastapi import Depends
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from websockets import Data

from models.content_model import ContentRequest,ContentSaveRequest, ReframeImageRequest, GeneratePostsRequest
from models.schedular_model import SchedularRequest

from services.gemini_service import generate_reformatted_image
from services.firebase_service import upload_image
from services.content_service import get_image_bytes
from services.gpt_service import generate_post_from_transcribed_text_func, generate_image_prompt

from controllers.company_controller import create_company_image

from google.cloud import firestore
from datetime import datetime, timezone
from utils.logger import setup_logger

from config.firebase_config import get_firestore_client

from cache.redis_config import  redis_list_get_all, redis_list_set_all
from cache.redis_config import redis_delete



logger = setup_logger("marketing-app")


router = APIRouter()


async def get_db():
    return get_firestore_client()




## generate posts for instagram
@router.post("/content/{company_id}/generate/instagram", tags=["Instagram content"])
async def generate_image_instagram(content: ContentRequest, company_id: str, db: firestore.Client = Depends(get_db)):
    try:
        planner_info={
            "image_prompt" : content.image_prompt,
            "company_id": company_id,
            "channel" : "instagram"
        }
        result = await create_company_image(planner_info)
        
        # Check if result is a JSONResponse (error case)
        if isinstance(result, JSONResponse):
            # Extract error details from JSONResponse
            error_content = result.body.decode('utf-8') if hasattr(result.body, 'decode') else str(result.body)
            try:
                error_dict = json.loads(error_content)
                error_msg = error_dict.get('message', 'Unknown error')
            except:
                error_msg = error_content
            raise HTTPException(status_code=result.status_code, detail=error_msg)
        
        logger.info(f"Content generation successful: {result}")

        ## maintain the count of images generated in the database
        year = datetime.now().year
        month = datetime.now().month
        usage_ref = db.collection("usage").document(company_id).collection(str(year)).document(str(month))
        usage_ref.set({
            "instagram_image_count": firestore.Increment(1)
        }, merge=True)


        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating image: {str(e)}")

## generate posts for facebook
@router.post("/content/{company_id}/generate/facebook", tags=["Facebook content"])
async def generate_image_facebook(content: ContentRequest, company_id: str, db: firestore.Client = Depends(get_db)):
    try:
        planner_info={
            "image_prompt" : content.image_prompt,
            "company_id": company_id,
            "channel" : "facebook"
        }
        result = await create_company_image(planner_info)
        
        # Check if result is a JSONResponse (error case)
        if isinstance(result, JSONResponse):
            # Extract error details from JSONResponse
            error_content = result.body.decode('utf-8') if hasattr(result.body, 'decode') else str(result.body)
            try:
                error_dict = json.loads(error_content)
                error_msg = error_dict.get('message', 'Unknown error')
            except:
                error_msg = error_content
            raise HTTPException(status_code=result.status_code, detail=error_msg)
        
        logger.info(f"Content generation successful: {result}")

        ## maintain the count of images generated in the database
        year = datetime.now().year
        month = datetime.now().month
        usage_ref = db.collection("usage").document(company_id).collection(str(year)).document(str(month))
        usage_ref.set({
            "facebook_image_count": firestore.Increment(1)
        }, merge=True)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating image: {str(e)}")

## generate posts for linkedin
@router.post("/content/{company_id}/generate/linkedin", tags=["LinkedIn content"])
async def generate_image_linkedin(content: ContentRequest, company_id: str, db: firestore.Client = Depends(get_db)):
    try:
        planner_info={
            "image_prompt" : content.image_prompt,
            "company_id": company_id,
            "channel" : "linkedin"
        }
        result = await create_company_image(planner_info)
        
        # Check if result is a JSONResponse (error case)
        if isinstance(result, JSONResponse):
            # Extract error details from JSONResponse
            error_content = result.body.decode('utf-8') if hasattr(result.body, 'decode') else str(result.body)
            try:
                error_dict = json.loads(error_content)
                error_msg = error_dict.get('message', 'Unknown error')
            except:
                error_msg = error_content
            raise HTTPException(status_code=result.status_code, detail=error_msg)
        
        logger.info(f"Content generation successful: {result}")

        ## maintain the count of images generated in the database
        year = datetime.now().year
        month = datetime.now().month
        usage_ref = db.collection("usage").document(company_id).collection(str(year)).document(str(month))
        usage_ref.set({
            "linkedin_image_count": firestore.Increment(1)
        }, merge=True)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating image: {str(e)}")

###################################################### Get posts ###################################################



@router.get("/content/{company_id}/instagram/post/{post_id}", tags=["Instagram content"])
def get_instagram_post(company_id: str, post_id: str, db: firestore.Client = Depends(get_db)):
    try:

        
        post_ref = db.collection("instagram_posts").document(company_id).collection("posts").document(post_id)
        post_doc = post_ref.get()

        if post_doc.exists:
            post_data = post_doc.to_dict()
            post_data["post_id"] = post_doc.id  
            status = post_data["status"]
            logger.info(f"Instagram post '{post_id}' fetched successfully")
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

@router.get("/content/{company_id}/facebook/post/{post_id}", tags=["Facebook content"])
def get_facebook_post(company_id: str, post_id: str, db: firestore.Client = Depends(get_db)):
    try:
        post_ref = db.collection("facebook_posts").document(company_id).collection("posts").document(post_id)
        post_doc = post_ref.get()

        if post_doc.exists:
            post_data = post_doc.to_dict()
            post_data["post_id"] = post_doc.id  
            status = post_data["status"]
            logger.info(f"Facebook post '{post_id}' fetched successfully")
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

@router.get("/content/{company_id}/linkedin/post/{post_id}", tags=["LinkedIn content"])
def get_linkedin_post(company_id: str, post_id: str, db: firestore.Client = Depends(get_db)):
    try:
        post_ref = db.collection("linkedin_posts").document(company_id).collection("posts").document(post_id)
        post_doc = post_ref.get()

        if post_doc.exists:
            post_data = post_doc.to_dict()
            post_data["post_id"] = post_doc.id  
            status = post_data["status"]
            logger.info(f"LinkedIn post '{post_id}' fetched successfully")
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
@router.get("/content/{company_id}/variation/{theme_index}", tags=["Post variation"])
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
        logger.info(f"Posts fetched successfully with variation and theme index")
        return {
            "data": posts_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching posts with variation and theme index for company {company_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching posts with variation and theme index: {str(e)}")

###################################################################################################################################

@router.get("/content/{company_id}/instagram/posts", tags=["Instagram content"])
async def get_all_instagram_posts(company_id: str, db: firestore.Client = Depends(get_db)):
    try:
        # Try to get from Redis list cache first
        posts_data = await redis_list_get_all(f"instagram_posts_{company_id}")
        if posts_data:
            logger.info(f"✅ Instagram posts fetched from Redis list cache for company {company_id} (count: {len(posts_data)})")
            return {
                "data": posts_data
            }

        logger.info(f"❌ Instagram posts not found in Redis list cache for company {company_id}, fetching from DB")

        posts_ref = db.collection("instagram_posts").document(company_id).collection("posts")
        
        posts = posts_ref.stream()
        
        posts_data = []
        for post in posts:
            post_data = post.to_dict()
            post_data["post_id"] = post.id
            posts_data.append(post_data)
        
        if posts_data:
            logger.info(f"All Instagram posts fetched successfully for company {company_id} (count: {len(posts_data)})")

            # Save posts to Redis list (with fallback)
            if await redis_list_set_all(f"instagram_posts_{company_id}", posts_data):
                logger.info(f"✅ Instagram posts saved to Redis list cache for company {company_id}")
            else:
                logger.warning(f"⚠️ Failed to save Instagram posts to Redis cache for company {company_id}, continuing anyway")
            
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
    
@router.get("/content/{company_id}/facebook/posts", tags=["Facebook content"])
async def get_all_facebook_posts(company_id: str, db: firestore.Client = Depends(get_db)):
    try:
        # Try to get from Redis list cache first
        posts_data = await redis_list_get_all(f"facebook_posts_{company_id}")
        if posts_data:
            logger.info(f"✅ Facebook posts fetched from Redis list cache for company {company_id} (count: {len(posts_data)})")
            return {
                "data": posts_data
            }

        logger.info(f"❌ Facebook posts not found in Redis list cache for company {company_id}, fetching from DB")

        posts_ref = db.collection("facebook_posts").document(company_id).collection("posts")
        
        posts = posts_ref.stream()
        
        posts_data = []
        for post in posts:
            post_data = post.to_dict()
            post_data["post_id"] = post.id
            posts_data.append(post_data)
        
        if posts_data:
            logger.info(f"All Facebook posts fetched successfully for company {company_id} (count: {len(posts_data)})")

            # Save posts to Redis list (with fallback)
            if await redis_list_set_all(f"facebook_posts_{company_id}", posts_data):
                logger.info(f"✅ Facebook posts saved to Redis list cache for company {company_id}")
            else:
                logger.warning(f"⚠️ Failed to save Facebook posts to Redis cache for company {company_id}, continuing anyway")
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
    
@router.get("/content/{company_id}/linkedin/posts", tags=["LinkedIn content"])
async def get_all_linkedin_posts(company_id: str, db: firestore.Client = Depends(get_db)):
    try:
        # Try to get from Redis list cache first
        posts_data = await redis_list_get_all(f"linkedin_posts_{company_id}")
        if posts_data:
            logger.info(f"✅ LinkedIn posts fetched from Redis list cache for company {company_id} (count: {len(posts_data)})")
            return {
                "data": posts_data
            }
            
        logger.info(f"❌ LinkedIn posts not found in Redis list cache for company {company_id}, fetching from DB")
            
        posts_ref = db.collection("linkedin_posts").document(company_id).collection("posts")
        
        posts = posts_ref.stream()
        
        posts_data = []
        for post in posts:
            post_data = post.to_dict()
            post_data["post_id"] = post.id
            posts_data.append(post_data)
        
        if posts_data:
            logger.info(f"All LinkedIn posts fetched successfully for company {company_id} (count: {len(posts_data)})")

            # Save posts to Redis list (with fallback)
            if await redis_list_set_all(f"linkedin_posts_{company_id}", posts_data):
                logger.info(f"✅ LinkedIn posts saved to Redis list cache for company {company_id}")
            else:
                logger.warning(f"⚠️ Failed to save LinkedIn posts to Redis cache for company {company_id}, continuing anyway")
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


#########################################################################################################


@router.post("/content/{company_id}/schedule/create", tags=["Scheduled posts"])
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

@router.post("/content/image/reformat", tags=["Image reformat"])
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






############################################### post save route ######################################################
@router.post("/content/{company_id}/instagram/save", tags=["Instagram content"])
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
        
        # STRATEGY 1: Invalidate cache instead of incremental update (more reliable)
        # This forces the next request to fetch fresh data from DB
        if await redis_delete(f"instagram_posts_{company_id}"):
            logger.info(f"✅ Instagram posts cache invalidated for company {company_id}")
        else:
            logger.warning(f"⚠️ Failed to invalidate Instagram posts cache for company {company_id}")
        
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


@router.post("/content/{company_id}/facebook/save", tags=["Facebook content"])
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
        
        # STRATEGY 1: Invalidate cache instead of incremental update (more reliable)
        if await redis_delete(f"facebook_posts_{company_id}"):
            logger.info(f"✅ Facebook posts cache invalidated for company {company_id}")
        else:
            logger.warning(f"⚠️ Failed to invalidate Facebook posts cache for company {company_id}")
        
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


@router.post("/content/{company_id}/linkedin/save", tags=["LinkedIn content"])
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
        
        # STRATEGY 1: Invalidate cache instead of incremental update (more reliable)
        if await redis_delete(f"linkedin_posts_{company_id}"):
            logger.info(f"✅ LinkedIn posts cache invalidated for company {company_id}")
        else:
            logger.warning(f"⚠️ Failed to invalidate LinkedIn posts cache for company {company_id}")
        
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


############################################# update post ###########################################
@router.put("/content/{company_id}/instagram/posts/{post_id}", tags=["Instagram content"])
async def update_instagram_post(company_id: str, post_id: str, content: ContentSaveRequest, db: firestore.Client = Depends(get_db)):
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

        update_data["updated_at"] = firestore.SERVER_TIMESTAMP
        
        if update_data:
            doc_ref.update(update_data)
            
            # STRATEGY 1: Invalidate cache (simpler and more reliable than list manipulation)
            if await redis_delete(f"instagram_posts_{company_id}"):
                logger.info(f"✅ Instagram posts cache invalidated for company {company_id}")
            else:
                logger.warning(f"⚠️ Failed to invalidate Instagram posts cache for company {company_id}")
            
            logger.info(f"Instagram post '{post_id}' updated successfully: {update_data}")
            return {
                "status": update_data["status"], 
                "message": f"Post {post_id} for Company {company_id} updated",
                "updated_fields": list(update_data.keys())
            }
        else:
            return {"status": update_data["status"], "message": "No fields to update"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Instagram post '{post_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating post: {str(e)}")


@router.put("/content/{company_id}/facebook/posts/{post_id}", tags=["Facebook content"])
async def update_facebook_post(company_id: str, post_id: str, content: ContentSaveRequest, db: firestore.Client = Depends(get_db)):
    try:
        doc_ref = db.collection("facebook_posts").document(company_id).collection("posts").document(post_id)
        
        doc_snapshot = doc_ref.get()
        if not doc_snapshot.exists:
            raise HTTPException(status_code=404, detail=f"Post {post_id} not found for company {company_id}")
        
        update_data = content.model_dump(exclude_unset=True)
        
        for field in ['caption', 'hashtags', 'scheduled_time', 'image_url', 'status']:
            if field in update_data and update_data[field] is None:
                update_data[field] = []
        if 'scheduled_time' in update_data:
            update_data["scheduled_datetime"] = datetime.fromisoformat(update_data["scheduled_time"].replace('Z', '+00:00'))
        
        update_data["updated_at"] = firestore.SERVER_TIMESTAMP
        
        if update_data:
            doc_ref.update(update_data)
            
            # STRATEGY 1: Invalidate cache
            if await redis_delete(f"facebook_posts_{company_id}"):
                logger.info(f"✅ Facebook posts cache invalidated for company {company_id}")
            else:
                logger.warning(f"⚠️ Failed to invalidate Facebook posts cache for company {company_id}")
            
            logger.info(f"Facebook post '{post_id}' updated successfully: {update_data}")
            return {
                "status": update_data["status"], 
                "message": f"Post {post_id} for Company {company_id} updated",
                "updated_fields": list(update_data.keys())
            }
        else:
            return {"status": update_data["status"], "message": "No fields to update"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Facebook post '{post_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating post: {str(e)}")

    
@router.put("/content/{company_id}/linkedin/posts/{post_id}", tags=["LinkedIn content"])
async def update_linkedin_post(company_id: str, post_id: str, content: ContentSaveRequest, db: firestore.Client = Depends(get_db)):
    try:
        doc_ref = db.collection("linkedin_posts").document(company_id).collection("posts").document(post_id)
        
        doc_snapshot = doc_ref.get()
        if not doc_snapshot.exists:
            raise HTTPException(status_code=404, detail=f"Post {post_id} not found for company {company_id}")
        
        update_data = content.model_dump(exclude_unset=True)
        
        for field in ['caption', 'hashtags', 'scheduled_time', 'image_url', 'status']:
            if field in update_data and update_data[field] is None:
                update_data[field] = []
        if 'scheduled_time' in update_data:
            update_data["scheduled_datetime"] = datetime.fromisoformat(update_data["scheduled_time"].replace('Z', '+00:00'))
        
        update_data["updated_at"] = firestore.SERVER_TIMESTAMP
        
        if update_data:
            doc_ref.update(update_data)
            
            # STRATEGY 1: Invalidate cache
            if await redis_delete(f"linkedin_posts_{company_id}"):
                logger.info(f"✅ LinkedIn posts cache invalidated for company {company_id}")
            else:
                logger.warning(f"⚠️ Failed to invalidate LinkedIn posts cache for company {company_id}")
            
            logger.info(f"LinkedIn post '{post_id}' updated successfully: {update_data}")
            return {
                "status": update_data["status"], 
                "message": f"Post {post_id} for Company {company_id} updated",
                "updated_fields": list(update_data.keys())
            }
        else:
            return {"status": update_data["status"], "message": "No fields to update"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating LinkedIn post '{post_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating post: {str(e)}")






############################################# delete post ###########################################
@router.delete("/content/{company_id}/instagram/posts/{post_id}", tags=["Instagram content"])
async def delete_instagram_post(company_id: str, post_id: str, db: firestore.Client = Depends(get_db)):
    try:
        doc_ref = db.collection("instagram_posts").document(company_id).collection("posts").document(post_id)
        doc_data = doc_ref.get().to_dict()
        if not doc_data:
            raise HTTPException(status_code=404, detail=f"Post {post_id} not found for company {company_id}")
        
        if doc_data["status"] == "published":
            raise HTTPException(status_code=400, detail=f"Post {post_id} is published and cannot be deleted")
        
        doc_ref.delete()
        #delete from redis
        if await redis_delete(f"instagram_posts_{company_id}"):
            logger.info(f"✅ Instagram posts cache invalidated for company {company_id}")
        else:
            logger.warning(f"⚠️ Failed to invalidate Instagram posts cache for company {company_id}")
        
        logger.info(f"Instagram post '{post_id}' deleted successfully")
        return {"status": "success", "message": "Post deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting Instagram post '{post_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting post: {str(e)}")


@router.delete("/content/{company_id}/facebook/posts/{post_id}", tags=["Facebook content"])
async def delete_facebook_post(company_id: str, post_id: str, db: firestore.Client = Depends(get_db)):
    try:
        doc_ref = db.collection("facebook_posts").document(company_id).collection("posts").document(post_id)
        doc_data = doc_ref.get().to_dict()
        if not doc_data:
            raise HTTPException(status_code=404, detail=f"Post {post_id} not found for company {company_id}")
        
        if doc_data["status"] == "published":
            raise HTTPException(status_code=400, detail=f"Post {post_id} is published and cannot be deleted")
        
        doc_ref.delete()
        #delete from redis
        if await redis_delete(f"facebook_posts_{company_id}"):
            logger.info(f"✅ Facebook posts cache invalidated for company {company_id}")
        else:
            logger.warning(f"⚠️ Failed to invalidate Facebook posts cache for company {company_id}")
        
        logger.info(f"Facebook post '{post_id}' deleted successfully")
        return {"status": "success", "message": "Post deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting Facebook post '{post_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting post: {str(e)}")


@router.delete("/content/{company_id}/linkedin/posts/{post_id}", tags=["LinkedIn content"])
async def delete_linkedin_post(company_id: str, post_id: str, db: firestore.Client = Depends(get_db)):
    try:
        doc_ref = db.collection("linkedin_posts").document(company_id).collection("posts").document(post_id)
        doc_data = doc_ref.get().to_dict()
        if not doc_data:
            raise HTTPException(status_code=404, detail=f"Post {post_id} not found for company {company_id}")
        
        if doc_data["status"] == "published":
            raise HTTPException(status_code=400, detail=f"Post {post_id} is published and cannot be deleted")
        
        doc_ref.delete()
        #delete from redis
        if await redis_delete(f"linkedin_posts_{company_id}"):
            logger.info(f"✅ LinkedIn posts cache invalidated for company {company_id}")
        else:
            logger.warning(f"⚠️ Failed to invalidate LinkedIn posts cache for company {company_id}")
        
        logger.info(f"LinkedIn post '{post_id}' deleted successfully")
        return {"status": "success", "message": "Post deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting LinkedIn post '{post_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting post: {str(e)}")



############################################# generate posts from transcribed text ###########################################
@router.post(
    "/content/generate/posts",
    tags=["post generation from transcribed text"]
 )
async def generate_posts_from_transcribed_text(
    request: GeneratePostsRequest,
    db: firestore.Client = Depends(get_db)
 ):
    try:
        # 1. Validate channel
        channel = request.channel.strip().lower()
        if channel not in ["instagram", "facebook", "linkedin"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid channel: {request.channel}. Must be one of: instagram, facebook, linkedin"
            )

        # 2. Fetch latest transcript for brand
        brand_name = request.brand_name.strip()
        if not brand_name:
            raise HTTPException(
                status_code=400,
                detail="Brand name cannot be empty"
            )
            
        logger.info(f"Searching for transcripts for brand: '{brand_name}'")
        
        # Query with exact case match
        transcripts_query = (
            db.collection("ai_journalist_transcripts")
            .where("data.Newsletter", "==", brand_name)
            .stream()
        )

        # Convert to list
        transcripts_list = list(transcripts_query)
        
        logger.info(f"Found {len(transcripts_list)} transcripts with exact match for '{brand_name}'")
        
        # If no exact match, try case-insensitive search
        if not transcripts_list:
            logger.info(f"No exact match for '{brand_name}'. Trying case-insensitive search...")
            
            all_transcripts = []
            all_docs = db.collection("ai_journalist_transcripts").stream()
            
            for doc in all_docs:
                doc_data = doc.to_dict()
                newsletter_field = doc_data.get("data", {}).get("Newsletter", "")
                
                if newsletter_field and newsletter_field.lower() == brand_name.lower():
                    all_transcripts.append(doc)
                    logger.info(f"Found case-insensitive match: '{newsletter_field}'")
            
            transcripts_list = all_transcripts
            
            if not transcripts_list:
                logger.warning(f"No transcripts found for brand '{brand_name}' (case-insensitive search)")
                raise HTTPException(
                    status_code=404,
                    detail=f"No transcript found for brand '{brand_name}'. Available brands might use different naming."
                )

        # Sort by created_at descending and get the latest one
        def get_sort_key(doc):
            doc_dict = doc.to_dict()
            created_at = doc_dict.get("created_at")
            
            if created_at is None:
                return datetime.min.replace(tzinfo=timezone.utc)
            
            # Handle DatetimeWithNanoseconds object (common in Firestore)
            if hasattr(created_at, 'year'):  # It's some kind of datetime object
                # For DatetimeWithNanoseconds, it's already comparable
                if created_at.tzinfo is None:
                    # If no timezone, assume UTC
                    return created_at.replace(tzinfo=timezone.utc)
                return created_at
            
            # If it's a regular Firestore Timestamp (less common in newer versions)
            elif hasattr(created_at, '_seconds'):
                from google.cloud import firestore as google_firestore
                if isinstance(created_at, google_firestore.timestamp.Timestamp):
                    return created_at.to_datetime().replace(tzinfo=timezone.utc)
            
            # For string timestamps
            elif isinstance(created_at, str):
                try:
                    return datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except ValueError:
                    return datetime.min.replace(tzinfo=timezone.utc)
                
            return datetime.min.replace(tzinfo=timezone.utc)

        transcripts_list.sort(key=get_sort_key, reverse=True)
        latest_transcript = transcripts_list[0]
        transcribed_data = latest_transcript.to_dict()

        logger.info(f"Using transcript ID: {latest_transcript.id} for brand '{brand_name}'")

        # Extract transcript text
        transcript_text = transcribed_data.get("data", {}).get("Transcript", "")
        
        if not transcript_text:
            logger.warning(f"Empty transcript found for brand '{brand_name}'")
            raise HTTPException(
                status_code=404,
                detail="Transcript text is empty or missing"
            )
            
        logger.info(f"Transcript text length: {len(transcript_text)} characters")

        # 3. Generate social post copy
        ai_result = await generate_post_from_transcribed_text_func(
            transcript_text=transcript_text,
            channel=channel
        )

        if not ai_result:
            logger.error("AI returned empty result")
            raise HTTPException(
                status_code=500,
                detail="AI failed to generate post content"
            )

        caption = ai_result.get("caption", "").strip()
        hashtags = ai_result.get("hashtags", [])
        cta = ai_result.get("cta", "").strip()
        
        # Validate AI result has content
        if not caption:
            logger.error("AI generated empty caption")
            raise HTTPException(
                status_code=500,
                detail="AI generated empty caption"
            )
            
        logger.info(f"Generated caption: {caption[:100]}...")
        logger.info(f"Generated hashtags: {hashtags}")

        # 4. Generate conceptual image prompt
        image_prompt_result = await generate_image_prompt(
            caption=caption,
            hashtags=hashtags,
            overlay_text=cta,
            image_analysis=None
        )

        if not image_prompt_result:
            logger.error("Image prompt generation returned empty result")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate image prompt"
            )
            
        image_prompt = image_prompt_result.get("image_prompt", "").strip()
        logger.info(f"Generated image prompt: {image_prompt[:100]}...")

        # 5. Response
        return {
            "caption": caption,
            "hashtags": hashtags,
            "cta": cta,
            "image_prompt": image_prompt,
            "brand_name": brand_name,
            "channel": channel,
            "transcript_id": latest_transcript.id,
            "transcript_date": str(transcribed_data.get("created_at")),
            "total_transcripts_found": len(transcripts_list)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error generating posts from transcribed text: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while generating post"
        )