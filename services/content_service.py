from datetime import datetime, timezone
from fastapi import Depends, HTTPException
from fastapi.responses import JSONResponse
import json
import calendar

from api.planner_routes import generate_instagram_planner, generate_facebook_planner, generate_linkedin_planner

from services.gpt_service import generate_newsletter, generate_blog

from uuid import uuid4
from config.firebase_config import get_firestore_client
from models.planner_model import PlannerRequest
from models.newsletter_model import NewsletterRequest
from models.blog_model import BlogRequest
from google.cloud import firestore

from cache.redis_config import redis_delete

from utils.logger import setup_logger
logger = setup_logger("marketing-app")

async def get_db():
    return get_firestore_client()


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
            company_ref = db.collection("companies").document(company_id)
            company_doc = company_ref.get()
            if not company_doc.exists:
                raise Exception("Company not found")
            company_data = company_doc.to_dict()

            if channel_name == "newsletter":
                
                # Get regional language from company data address if available
                regional_language = None
                
                
                newsletter_request = NewsletterRequest(
                    theme=planner_request.theme_title,
                    theme_description=planner_request.theme_description,
                )
                
                # generate_newsletter is not async, so don't use await
                newsletter = generate_newsletter(
                    company_data, 
                    newsletter_request.theme, 
                    newsletter_request.theme_description,
                    regional_language
                )
                if not newsletter:
                    raise Exception("Newsletter returned None")

                newsletter_id = uuid4().hex
                # Remove token_usage before saving
                newsletter_for_storage = newsletter.copy()
                newsletter_for_storage.pop("token_usage", None)
                
                doc_data = {
                    "company_id": company_id,
                    "newsletter_id": newsletter_id,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                    "status": "draft",
                    "scheduled_time": None,
                    "scheduled_datetime": None,
                    "month_id": month_id,
                    "response": newsletter_for_storage,
                }
                newsletter_doc_ref = db.collection("channels").document("newsletter").collection("companies").document(company_id).collection("newsletters").document(newsletter_id)
                newsletter_doc_ref.set(doc_data)
                posts.append(newsletter_id)
                logger.info(f"✅ Generated newsletter {count+1}/{post_count} with ID: {newsletter_id}")

            elif channel_name == "blog":
                # Get regional language from company data address if available
                regional_language = None
                
                
                blog_request = BlogRequest(
                    theme=planner_request.theme_title,
                    theme_description=planner_request.theme_description,
                )
                
                # generate_blog is not async, so don't use await
                blog = generate_blog(
                    company_data, 
                    blog_request.theme, 
                    blog_request.theme_description,
                    regional_language
                )
                if not blog:
                    raise Exception("Blog returned None")
                    
                blog_id = uuid4().hex
                # Remove token_usage before saving
                blog_for_storage = blog.copy()
                blog_for_storage.pop("token_usage", None)
                
                doc_data = {
                    "company_id": company_id,
                    "blog_id": blog_id,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                    "status": "draft",
                    "scheduled_time": None,
                    "scheduled_datetime": None,
                    "month_id": month_id,
                    "response": blog_for_storage,
                }
                blog_doc_ref = db.collection("channels").document("blog").collection("companies").document(company_id).collection("blogs").document(blog_id)
                blog_doc_ref.set(doc_data)
                posts.append(blog_id)
                logger.info(f"✅ Generated blog {count+1}/{post_count} with ID: {blog_id}")


            else:
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
                
                # Handle case where image_result might be a JSONResponse (error case)
                if isinstance(image_result, JSONResponse):
                    # Extract error details from JSONResponse
                    try:
                        error_content = image_result.body.decode('utf-8') if hasattr(image_result.body, 'decode') else str(image_result.body)
                        error_dict = json.loads(error_content)
                        error_msg = error_dict.get('message', 'Unknown error during image generation')
                    except:
                        error_msg = f"Image generation failed with status {image_result.status_code}"
                    raise Exception(f"Image generation error: {error_msg}")
                
                # Ensure image_result is a dict before calling .get()
                if not isinstance(image_result, dict):
                    raise Exception(f"Unexpected image_result type: {type(image_result)}, expected dict")
                
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
    #invalidate cache
    if await redis_delete(f"{channel_name}_posts_{company_id}"):
        logger.info(f"✅ {channel_name}_posts cache invalidated for company {company_id}")
    else:
        logger.warning(f"⚠️ Failed to invalidate {channel_name}_posts cache for company {company_id}")
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

    if not posts:
        return True
    
    ## figure out the year
    year = datetime.now().year
    if int(month_id) < datetime.now().month:
        year = datetime.now().year + 1
    else:
        year = datetime.now().year

    total_days = month_days[int(month_id)]

    # Calculate spacing between posts
    spacing = total_days / len(posts)

    # Generate a date for each post
    for index, post_id in enumerate(posts):

        # Calculate which day this post should be scheduled on
        day_offset = int(index * spacing)
        day = min(day_offset + 1, total_days)  

        scheduled_time = datetime(year, int(month_id), day, 10, 0, tzinfo=timezone.utc).isoformat()
        scheduled_datetime = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))

        # Newsletter and blog use different Firestore structure
        if channel_name == "newsletter":
            doc_ref = (
                db.collection("channels")
                .document("newsletter")
                .collection("companies")
                .document(company_id)
                .collection("newsletters")
                .document(post_id)
            )
        elif channel_name == "blog":
            doc_ref = (
                db.collection("channels")
                .document("blog")
                .collection("companies")
                .document(company_id)
                .collection("blogs")
                .document(post_id)
            )
        else:
            # Regular social media posts (instagram, facebook, linkedin)
            doc_ref = (
                db.collection(f"{channel_name}_posts")
                .document(company_id)
                .collection("posts")
                .document(post_id)
            )

        doc_ref.update({
            "scheduled_time": scheduled_time,
            "scheduled_datetime": scheduled_datetime,
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
        facebook_post_count = channel_config.get('facebook_post_count', 1)
        instagram_post_count = channel_config.get('instagram_post_count', 1)
        linkedin_post_count = channel_config.get('linkedin_post_count', 1)
        newsletter_post_count = channel_config.get('email_campaign_count', 1)
        blog_post_count = channel_config.get('blog_post_count', 1)

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
            f"Instagram: {instagram_post_count}, Facebook: {facebook_post_count}, LinkedIn: {linkedin_post_count}, "
            f"Newsletter: {newsletter_post_count}, Blog: {blog_post_count}"
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

        newsletter_task = generate_channel_posts(
            "newsletter", newsletter_post_count, company_id, planner_request, month_id, theme_index, scheduled_month, db,
            None, None  # newsletter doesn't use planner or image functions
        )   
        blog_task = generate_channel_posts(
            "blog", blog_post_count, company_id, planner_request, month_id, theme_index, scheduled_month, db,
            None, None  # blog doesn't use planner or image functions
        )

        # Run all tasks in parallel and wait for completion
        insta_posts, fb_posts, linkedin_posts ,newsletter_posts, blog_posts= await asyncio.gather(
            instagram_task,
            facebook_task,
            linkedin_task,
            newsletter_task,
            blog_task
        )


        # Spread posts over month
        await asyncio.gather(
            spread_posts_over_month(insta_posts, month_id, "instagram", company_id, db),
            spread_posts_over_month(fb_posts, month_id, "facebook", company_id, db),
            spread_posts_over_month(linkedin_posts, month_id, "linkedin", company_id, db),
            spread_posts_over_month(newsletter_posts, month_id, "newsletter", company_id, db),
            spread_posts_over_month(blog_posts, month_id, "blog", company_id, db),
        )

        # Combine all post IDs
        all_posts = insta_posts + fb_posts + linkedin_posts + newsletter_posts + blog_posts

        logger.info(f"🎯 Successfully generated {len(all_posts)} total posts for company {company_id}")
        logger.debug(
            f"Post ID summary for company {company_id}: "
            f"instagram={insta_posts}, facebook={fb_posts}, linkedin={linkedin_posts}, newsletter={newsletter_posts}, blog={blog_posts}"
        )

        return {
            "status": "success",
            "post_ids": all_posts,
            "counts": {
                "instagram": len(insta_posts),
                "facebook": len(fb_posts),
                "linkedin": len(linkedin_posts),
                "newsletter": len(newsletter_posts),
                "blog": len(blog_posts)
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
