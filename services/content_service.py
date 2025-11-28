from datetime import datetime, timezone
from fastapi import Depends, HTTPException

from api.planner_routes import generate_instagram_planner, generate_facebook_planner, generate_linkedin_planner

from config.firebase_config import get_firestore_client
from models.planner_model import PlannerRequest

from google.cloud import firestore

from utils.logger import setup_logger
logger = setup_logger("marketing-app")

async def get_db():
    return get_firestore_client()


# async def generate_scheduled_posts(company_id: str, posts_data: dict, db: firestore.Client = Depends(get_db)):
#     try:
#         channel_config_ref = db.collection("channel_config").document(company_id).get()
#         if not channel_config_ref.exists:
#             raise HTTPException(status_code=404, detail=f"Channel config not found for company {company_id}")
#         channel_config = channel_config_ref.to_dict()  


#         facebook_post_count = channel_config.get('facebook_post_count', 0)
#         instagram_post_count = channel_config.get('instagram_post_count', 0)
#         linkedin_post_count = channel_config.get('linkedin_post_count', 0)
#         theme = posts_data.get('theme')
#         theme_description = posts_data.get('theme_description')
#         scheduled_month = posts_data.get('scheduled_month')

#         month_id = posts_data.get('month_id')
#         theme_index = posts_data.get('theme_index')
        
#         # FIX: Create proper Pydantic model objects instead of raw dictionaries
#         planner_request = PlannerRequest(
#             theme_title=theme,
#             theme_description=theme_description
#         )

#         all_posts = []

#         logger.info(
#             f"Generating scheduled posts for company {company_id} | "
#             f"Instagram: {instagram_post_count}, Facebook: {facebook_post_count}, LinkedIn: {linkedin_post_count}"
#         )
#         logger.debug(
#             f"Planner request payload for company {company_id}: "
#             f"theme='{theme}', theme_description='{theme_description}', scheduled_month='{scheduled_month}'"
#         )

        
#         insta_posts = []
#         # generate insta posts
#         for count in range(instagram_post_count):
#             try:
#                 logger.info(f"Generating Instagram post {count+1}")
#                 logger.debug(f"[Instagram:{count+1}] Calling planner with payload: {planner_request.dict()}")
                
#                 # FIX: Pass the Pydantic model, not a dictionary
#                 planner = await generate_instagram_planner(planner_request, company_id)
#                 if not planner:
#                     raise Exception("Planner returned None")
                
#                 logger.info(f"Instagram planner result received")
#                 logger.debug(f"[Instagram:{count+1}] Planner response keys: {list(planner.keys())}")
                
#                 # generate image for post - FIX: Use proper content request model
#                 from models.content_model import ContentRequest
#                 image_prompt = planner.get('image_prompt')
#                 if not image_prompt:
#                     raise Exception("No image prompt returned from planner")
                
#                 # Create proper ContentRequest
#                 content_request = ContentRequest(image_prompt=image_prompt)
#                 logger.debug(
#                     f"[Instagram:{count+1}] Image prompt preview: {image_prompt[:120]}{'...' if len(image_prompt) > 120 else ''}"
#                 )
#                 image_result = await generate_image_instagram(content_request, company_id)
#                 image_url = image_result.get('image_url')
                
#                 if not image_url:
#                     raise Exception("No image URL returned from image generation")
                
#                 # save post to db - FIX: Use proper ContentSaveRequest
            
#                 logger.debug(f"[Instagram:{count+1}] Firestore client initialized for company {company_id}")
#                 post_data = {
#                     "company_id": company_id,
#                     "channel": "instagram",  
#                     "image_url": image_url,
#                     "caption": planner.get('caption', ''),
#                     "hashtags": planner.get('hashtags', []),
#                     "overlay_text": planner.get('overlay_text', ''),
#                     "status" : "draft",

#                     "month_id": month_id,
#                     "theme_index": theme_index,

#                     "scheduled_month": scheduled_month,
#                     "created_at": datetime.now(timezone.utc),
#                     "updated_at": datetime.now(timezone.utc)
#                 }

#                 # check if post with same theme and month already exists, if yes then increment the variation index
#                 existing_posts = list(db.collection('instagram_posts').document(company_id).collection('posts').where("month_id", "==", month_id).where("theme_index", "==", theme_index).stream())
#                 variation_index = len(existing_posts)
#                 if variation_index > 0:
#                     variation_index = variation_index + 1
#                 else:
#                     variation_index = 1
#                 post_data["variation_index"] = variation_index

#                 doc_ref = db.collection('instagram_posts').document(company_id).collection('posts').add(post_data)
#                 post_id = doc_ref[1].id
#                 insta_posts.append(post_id)
#                 logger.debug(
#                     f"[Instagram:{count+1}] Post data keys persisted: {list(post_data.keys())} | Firestore doc path: instagram_posts/{company_id}/posts/{post_id}"
#                 )
#                 logger.info(f"✅ Generated Instagram post {count+1}/{instagram_post_count} with ID: {post_id}")

#             except Exception as e:
#                 logger.error(f"Failed to generate Instagram post {count+1}: {str(e)}", exc_info=True)
#                 raise HTTPException(status_code=500, detail=f"Couldn't generate Instagram post number {count+1} for company {company_id}: {str(e)}")

#         fb_posts = []
#         # generate fb posts
#         for count in range(facebook_post_count):
#             try:
#                 logger.info(f"Generating Facebook post {count+1}")
#                 logger.debug(f"[Facebook:{count+1}] Calling planner with payload: {planner_request.dict()}")
                
#                 # FIX: Pass the Pydantic model
#                 planner = await generate_facebook_planner(planner_request, company_id)
#                 if not planner:
#                     raise Exception("Planner returned None")
                
#                 # generate image for post
#                 image_prompt = planner.get('image_prompt')
#                 if not image_prompt:
#                     raise Exception("No image prompt returned from planner")
                
#                 # Create proper ContentRequest
#                 content_request = ContentRequest(image_prompt=image_prompt)
#                 logger.debug(
#                     f"[Facebook:{count+1}] Image prompt preview: {image_prompt[:120]}{'...' if len(image_prompt) > 120 else ''}"
#                 )
#                 image_result = await generate_image_facebook(content_request, company_id)
#                 image_url = image_result.get('image_url')
                
#                 if not image_url:
#                     raise Exception("No image URL returned from image generation")
                
#                 # save post to db
                
#                 logger.debug(f"[Facebook:{count+1}] Firestore client initialized for company {company_id}")
#                 post_data = {
#                     "company_id": company_id,
#                     "channel": "facebook",  
#                     "image_url": image_url,
#                     "caption": planner.get('caption', ''),
#                     "hashtags": planner.get('hashtags', []),
#                     "overlay_text": planner.get('overlay_text', ''),
#                     "status" : "draft",

#                     "month_id": month_id,
#                     "theme_index": theme_index,

#                     "scheduled_month": scheduled_month,
#                     "created_at": datetime.now(timezone.utc),
#                     "updated_at": datetime.now(timezone.utc)
#                 }

#                 # check if post with same theme and month already exists, if yes then increment the variation index
#                 existing_posts = list(db.collection('facebook_posts').document(company_id).collection('posts').where("month_id", "==", month_id).where("theme_index", "==", theme_index).stream())
#                 variation_index = len(existing_posts)
#                 if variation_index > 0:
#                     variation_index = variation_index + 1
#                 else:
#                     variation_index = 1
#                 post_data["variation_index"] = variation_index

#                 doc_ref = db.collection('facebook_posts').document(company_id).collection('posts').add(post_data)
#                 post_id = doc_ref[1].id
#                 fb_posts.append(post_id)
#                 logger.debug(
#                     f"[Facebook:{count+1}] Post data keys persisted: {list(post_data.keys())} | Firestore doc path: facebook_posts/{company_id}/posts/{post_id}"
#                 )
        
#                 logger.info(f"✅ Generated Facebook post {count+1}/{facebook_post_count} with ID: {post_id}")

#             except Exception as e:
#                 logger.error(f"Failed to generate Facebook post {count+1}: {str(e)}", exc_info=True)
#                 raise HTTPException(status_code=500, detail=f"Couldn't generate Facebook post number {count+1} for company {company_id}: {str(e)}")

#         linkedin_posts = []
#         # generate linkedin posts
#         for count in range(linkedin_post_count):
#             try:
#                 logger.info(f"Generating LinkedIn post {count+1}")
#                 logger.debug(f"[LinkedIn:{count+1}] Calling planner with payload: {planner_request.dict()}")
                
#                 # FIX: Pass the Pydantic model
#                 planner = await generate_linkedin_planner(planner_request, company_id)
#                 if not planner:
#                     raise Exception("Planner returned None")
                
#                 # generate image for post
#                 image_prompt = planner.get('image_prompt')
#                 if not image_prompt:
#                     raise Exception("No image prompt returned from planner")
                
#                 # Create proper ContentRequest
#                 content_request = ContentRequest(image_prompt=image_prompt)
#                 logger.debug(
#                     f"[LinkedIn:{count+1}] Image prompt preview: {image_prompt[:120]}{'...' if len(image_prompt) > 120 else ''}"
#                 )
#                 image_result = await generate_image_linkedin(content_request, company_id)
#                 image_url = image_result.get('image_url')
                
#                 if not image_url:
#                     raise Exception("No image URL returned from image generation")
                
#                 # save post to db
            
                
#                 logger.debug(f"[LinkedIn:{count+1}] Firestore client initialized for company {company_id}")
#                 post_data = {
#                     "company_id": company_id,
#                     "channel": "linkedin",  
#                     "image_url": image_url,
#                     "caption": planner.get('caption', ''),
#                     "hashtags": planner.get('hashtags', []),
#                     "status" : "draft",

#                     "month_id": month_id,
#                     "theme_index": theme_index,

#                     "overlay_text": planner.get('overlay_text', ''),
#                     "scheduled_month": scheduled_month,
#                     "created_at": datetime.now(timezone.utc),
#                     "updated_at": datetime.now(timezone.utc)
#                 }
                
#                 # check if post with same theme and month already exists, if yes then increment the variation index
#                 existing_posts = list(db.collection('linkedin_posts').document(company_id).collection('posts').where("month_id", "==", month_id).where("theme_index", "==", theme_index).stream())
#                 variation_index = len(existing_posts)
#                 if variation_index > 0:
#                     variation_index = variation_index + 1
#                 else:
#                     variation_index = 1
#                 post_data["variation_index"] = variation_index

#                 doc_ref = db.collection('linkedin_posts').document(company_id).collection('posts').add(post_data)
#                 post_id = doc_ref[1].id
#                 linkedin_posts.append(post_id)
#                 logger.debug(
#                     f"[LinkedIn:{count+1}] Post data keys persisted: {list(post_data.keys())} | Firestore doc path: linkedin_posts/{company_id}/posts/{post_id}"
#                 )
                
#                 logger.info(f"✅ Generated LinkedIn post {count+1}/{linkedin_post_count} with ID: {post_id}")

#             except Exception as e:
#                 logger.error(f"Failed to generate LinkedIn post {count+1}: {str(e)}", exc_info=True)
#                 raise HTTPException(status_code=500, detail=f"Couldn't generate LinkedIn post number {count+1} for company {company_id}: {str(e)}")
            
#         # Combine all post IDs
#         all_posts = insta_posts + fb_posts + linkedin_posts

#         logger.info(f"🎯 Successfully generated {len(all_posts)} total posts for company {company_id}")
#         logger.debug(
#             f"Post ID summary for company {company_id}: "
#             f"instagram={insta_posts}, facebook={fb_posts}, linkedin={linkedin_posts}"
#         )

#         return {
#             "status": "success",
#             "post_ids": all_posts,
#             "counts": {
#                 "instagram": len(insta_posts),
#                 "facebook": len(fb_posts),
#                 "linkedin": len(linkedin_posts)
#             }
#         }
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Failed to generate scheduled posts: {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Failed to generate scheduled posts: {str(e)}")



import asyncio

async def generate_channel_posts(
        channel_name: str,
        post_count: int,
        company_id: str,
        planner_request,
        month_id: str,
        theme_index: int,
        scheduled_month: str,
        db: firestore.Client,
        generate_planner_func,
        generate_image_func
    ):
    """Helper function to generate posts for a single channel"""
    posts = []
    collection_name = f"{channel_name}_posts"
    
    for count in range(post_count):
        try:
            logger.info(f"Generating {channel_name.title()} post {count+1}")
            logger.debug(f"[{channel_name.title()}:{count+1}] Calling planner with payload: {planner_request.dict()}")
            
            # Generate planner - pass db instance
            planner = await generate_planner_func(planner_request, company_id, db)
            if not planner:
                raise Exception("Planner returned None")
            
            logger.info(f"{channel_name.title()} planner result received")
            logger.debug(f"[{channel_name.title()}:{count+1}] Planner response keys: {list(planner.keys())}")
            
            # Generate image
            from models.content_model import ContentRequest
            image_prompt = planner.get('image_prompt')
            if not image_prompt:
                raise Exception("No image prompt returned from planner")
            
            content_request = ContentRequest(image_prompt=image_prompt)
            logger.debug(
                f"[{channel_name.title()}:{count+1}] Image prompt preview: {image_prompt[:120]}{'...' if len(image_prompt) > 120 else ''}"
            )
            
            image_result = await generate_image_func(content_request, company_id)
            image_url = image_result.get('image_url')
            
            if not image_url:
                raise Exception("No image URL returned from image generation")
            
            # Prepare post data
            logger.debug(f"[{channel_name.title()}:{count+1}] Firestore client initialized for company {company_id}")
            post_data = {
                "company_id": company_id,
                "channel": channel_name,
                "image_url": image_url,
                "caption": planner.get('caption', ''),
                "hashtags": planner.get('hashtags', []),
                "overlay_text": planner.get('overlay_text', ''),
                "status": "draft",
                "month_id": month_id,
                "theme_index": theme_index,
                "scheduled_month": scheduled_month,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            
            # Check for existing posts and set variation index
            existing_posts = list(
                db.collection(collection_name)
                .document(company_id)
                .collection('posts')
                .where("month_id", "==", month_id)
                .where("theme_index", "==", theme_index)
                .stream()
            )
            variation_index = len(existing_posts)
            if variation_index > 0:
                variation_index = variation_index + 1
            else:
                variation_index = 1
            post_data["variation_index"] = variation_index
            
            # Save to Firestore
            doc_ref = db.collection(collection_name).document(company_id).collection('posts').add(post_data)
            post_id = doc_ref[1].id
            posts.append(post_id)
            
            logger.debug(
                f"[{channel_name.title()}:{count+1}] Post data keys persisted: {list(post_data.keys())} | "
                f"Firestore doc path: {collection_name}/{company_id}/posts/{post_id}"
            )
            logger.info(f"✅ Generated {channel_name.title()} post {count+1}/{post_count} with ID: {post_id}")
            
        except Exception as e:
            logger.error(f"Failed to generate {channel_name.title()} post {count+1}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Couldn't generate {channel_name.title()} post number {count+1} for company {company_id}: {str(e)}"
            )
    
    return posts



#################################################### spread posts over month ##################################################
month_days = {
    1: 31,
    2: 28,
    3: 31,
    4: 30,
    5: 31,
    6: 30,
    7: 31,
    8: 31,
    9: 30,
    10: 31,
    11: 30,
    12: 31,
}
async def spread_posts_over_month(posts: list, month_id: str, channel_name: str, company_id: str, db: firestore.Client):

    ## figure out the year
    year = datetime.now().year
    if int(month_id) < datetime.now().month:
        year = datetime.now().year + 1
    else:
        year = datetime.now().year



    total_days = month_days[month_id]

    # Calculate spacing between posts
    spacing = total_days / len(posts)

    # Generate a date for each post
    for index, post_id in enumerate(posts):

        # Calculate which day this post should be scheduled on
        day_offset = int(index * spacing)
        day = min(day_offset + 1, total_days)  

        scheduled_time = datetime(year, month_id, day, 10, 0, tzinfo=timezone.utc).isoformat()

        doc_ref = (
            db.collection(f"{channel_name}_posts")
              .document(company_id)
              .collection("posts")
              .document(post_id)
        )

        doc_ref.update({
            "scheduled_time": scheduled_time,
            "scheduled_datetime": datetime.fromisoformat(scheduled_time.replace('Z', '+00:00')),
            "updated_at": firestore.SERVER_TIMESTAMP,
        })

        await asyncio.sleep(0.05)  

    return True

#################################################### generate scheduled posts ##################################################

async def generate_scheduled_posts(company_id: str, posts_data: dict, db: firestore.Client):
    try:
        # Fetch channel config
        channel_config_ref = db.collection("channel_config").document(company_id).get()
        if not channel_config_ref.exists:
            raise HTTPException(status_code=404, detail=f"Channel config not found for company {company_id}")
        channel_config = channel_config_ref.to_dict()

        # Extract configuration
        facebook_post_count = channel_config.get('facebook_post_count', 0)
        instagram_post_count = channel_config.get('instagram_post_count', 0)
        linkedin_post_count = channel_config.get('linkedin_post_count', 0)
        theme = posts_data.get('theme')
        theme_description = posts_data.get('theme_description')
        scheduled_month = posts_data.get('scheduled_month')
        month_id = posts_data.get('month_id')
        theme_index = posts_data.get('theme_index')
        
        # Create Pydantic model
        planner_request = PlannerRequest(
            theme_title=theme,
            theme_description=theme_description
        )

        logger.info(
            f"Generating scheduled posts for company {company_id} | "
            f"Instagram: {instagram_post_count}, Facebook: {facebook_post_count}, LinkedIn: {linkedin_post_count}"
        )
        logger.debug(
            f"Planner request payload for company {company_id}: "
            f"theme='{theme}', theme_description='{theme_description}', scheduled_month='{scheduled_month}'"
        )

        # Lazy import to avoid circular dependency
        from api.content_routes import generate_image_instagram, generate_image_facebook, generate_image_linkedin

        # Generate posts for all channels in parallel
        instagram_task = generate_channel_posts(
            "instagram", instagram_post_count, company_id, planner_request,
            month_id, theme_index, scheduled_month, db,
            generate_instagram_planner, generate_image_instagram
        )
        
        
        facebook_task = generate_channel_posts(
            "facebook", facebook_post_count, company_id, planner_request,
            month_id, theme_index, scheduled_month, db,
            generate_facebook_planner, generate_image_facebook
        )

       

        linkedin_task = generate_channel_posts(
            "linkedin", linkedin_post_count, company_id, planner_request,
            month_id, theme_index, scheduled_month, db,
            generate_linkedin_planner, generate_image_linkedin
        )
        
        # Run all tasks in parallel and wait for completion
        insta_posts, fb_posts, linkedin_posts = await asyncio.gather(
            instagram_task,
            facebook_task,
            linkedin_task
        )


        # Spread posts over month
        await asyncio.gather(
            spread_posts_over_month(insta_posts, month_id, "instagram", company_id, db),
            spread_posts_over_month(fb_posts, month_id, "facebook", company_id, db),
            spread_posts_over_month(linkedin_posts, month_id, "linkedin", company_id, db)
        )

        # Combine all post IDs
        all_posts = insta_posts + fb_posts + linkedin_posts

        logger.info(f"🎯 Successfully generated {len(all_posts)} total posts for company {company_id}")
        logger.debug(
            f"Post ID summary for company {company_id}: "
            f"instagram={insta_posts}, facebook={fb_posts}, linkedin={linkedin_posts}"
        )

        return {
            "status": "success",
            "post_ids": all_posts,
            "counts": {
                "instagram": len(insta_posts),
                "facebook": len(fb_posts),
                "linkedin": len(linkedin_posts)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate scheduled posts: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate scheduled posts: {str(e)}")





#################################################### reframing post ##################################################

import requests
import base64
from typing import Tuple

# Constants for image processing
IMAGE_DOWNLOAD_TIMEOUT = 30  # seconds
MIN_IMAGE_SIZE = 1024  # 1 KB minimum

async def get_image_bytes(image_url: str) -> bytes:
    """
    Download image from URL and return as base64-encoded string.
    Optimized for memory efficiency with streaming and timeout.
    """
    try:
        # Use streaming and timeout to prevent memory issues and hanging requests
        response = requests.get(
            image_url,
            stream=True,
            timeout=IMAGE_DOWNLOAD_TIMEOUT,
            headers={'User-Agent': 'Marketing-App/1.0'}
        )
        response.raise_for_status()
        
        # Read content in chunks to avoid loading entire image into memory at once
        content = bytearray()
        for chunk in response.iter_content(chunk_size=8192):  # 8KB chunks
            if chunk:
                content.extend(chunk)
        
        # Convert to base64 string (required by Gemini API)
        image_bytes = base64.b64encode(bytes(content)).decode('utf-8')
        return image_bytes
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download image from {image_url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download image: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to process image bytes from {image_url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")
