from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import HTTPException
from api.planner_routes import generate_instagram_planner, generate_facebook_planner, generate_linkedin_planner
from api.content_routes import generate_image_instagram, generate_image_facebook, generate_image_linkedin

from config.firebase_config import get_firestore_client

from models.planner_model import PlannerRequest

from utils.logger import setup_logger
logger = setup_logger("marketing-app")

async def generate_scheduled_posts(company_id: str, posts_data: dict):
    try:
        facebook_post_count = posts_data.get('facebook_post_count', 0)
        instagram_post_count = posts_data.get('instagram_post_count', 0)
        linkedin_post_count = posts_data.get('linkedin_post_count', 0)
        theme = posts_data.get('theme')
        theme_description = posts_data.get('theme_description')
        scheduled_month = posts_data.get('scheduled_month')

        # FIX: Create proper Pydantic model objects instead of raw dictionaries
        planner_request = PlannerRequest(
            theme_title=theme,
            theme_description=theme_description
        )

        all_posts = []

        logger.info(
            f"Generating scheduled posts for company {company_id} | "
            f"Instagram: {instagram_post_count}, Facebook: {facebook_post_count}, LinkedIn: {linkedin_post_count}"
        )
        logger.debug(
            f"Planner request payload for company {company_id}: "
            f"theme='{theme}', theme_description='{theme_description}', scheduled_month='{scheduled_month}'"
        )

        
        insta_posts = []
        # generate insta posts
        for count in range(instagram_post_count):
            try:
                logger.info(f"Generating Instagram post {count+1}")
                logger.debug(f"[Instagram:{count+1}] Calling planner with payload: {planner_request.dict()}")
                
                # FIX: Pass the Pydantic model, not a dictionary
                planner = await generate_instagram_planner(planner_request, company_id)
                if not planner:
                    raise Exception("Planner returned None")
                
                logger.info(f"Instagram planner result received")
                logger.debug(f"[Instagram:{count+1}] Planner response keys: {list(planner.keys())}")
                
                # generate image for post - FIX: Use proper content request model
                from models.content_model import ContentRequest
                image_prompt = planner.get('image_prompt')
                if not image_prompt:
                    raise Exception("No image prompt returned from planner")
                
                # Create proper ContentRequest
                content_request = ContentRequest(image_prompt=image_prompt)
                logger.debug(
                    f"[Instagram:{count+1}] Image prompt preview: {image_prompt[:120]}{'...' if len(image_prompt) > 120 else ''}"
                )
                image_result = await generate_image_instagram(content_request, company_id)
                image_url = image_result.get('image_url')
                
                if not image_url:
                    raise Exception("No image URL returned from image generation")
                
                # save post to db - FIX: Use proper ContentSaveRequest
            
                db = get_firestore_client()
                logger.debug(f"[Instagram:{count+1}] Firestore client initialized for company {company_id}")
                post_data = {
                    "company_id": company_id,
                    "channel": "instagram",  
                    "image_url": image_url,
                    "caption": planner.get('caption', ''),
                    "hashtags": planner.get('hashtags', []),
                    "overlay_text": planner.get('overlay_text', ''),
                    "status" : "draft",
                    "scheduled_month": scheduled_month,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }

                doc_ref = db.collection('instagram_posts').document(company_id).collection('posts').add(post_data)
                post_id = doc_ref[1].id
                insta_posts.append(post_id)
                logger.debug(
                    f"[Instagram:{count+1}] Post data keys persisted: {list(post_data.keys())} | Firestore doc path: instagram_posts/{company_id}/posts/{post_id}"
                )
                logger.info(f"✅ Generated Instagram post {count+1}/{instagram_post_count} with ID: {post_id}")

            except Exception as e:
                logger.error(f"Failed to generate Instagram post {count+1}: {str(e)}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Couldn't generate Instagram post number {count+1} for company {company_id}: {str(e)}")

        fb_posts = []
        # generate fb posts
        for count in range(facebook_post_count):
            try:
                logger.info(f"Generating Facebook post {count+1}")
                logger.debug(f"[Facebook:{count+1}] Calling planner with payload: {planner_request.dict()}")
                
                # FIX: Pass the Pydantic model
                planner = await generate_facebook_planner(planner_request, company_id)
                if not planner:
                    raise Exception("Planner returned None")
                
                # generate image for post
                image_prompt = planner.get('image_prompt')
                if not image_prompt:
                    raise Exception("No image prompt returned from planner")
                
                # Create proper ContentRequest
                content_request = ContentRequest(image_prompt=image_prompt)
                logger.debug(
                    f"[Facebook:{count+1}] Image prompt preview: {image_prompt[:120]}{'...' if len(image_prompt) > 120 else ''}"
                )
                image_result = await generate_image_facebook(content_request, company_id)
                image_url = image_result.get('image_url')
                
                if not image_url:
                    raise Exception("No image URL returned from image generation")
                
                # save post to db
                
            
                db = get_firestore_client()
                logger.debug(f"[Facebook:{count+1}] Firestore client initialized for company {company_id}")
                post_data = {
                    "company_id": company_id,
                    "channel": "facebook",  
                    "image_url": image_url,
                    "caption": planner.get('caption', ''),
                    "hashtags": planner.get('hashtags', []),
                    "overlay_text": planner.get('overlay_text', ''),
                    "status" : "draft",
                    "scheduled_month": scheduled_month,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }

                doc_ref = db.collection('facebook_posts').document(company_id).collection('posts').add(post_data)
                post_id = doc_ref[1].id
                fb_posts.append(post_id)
                logger.debug(
                    f"[Facebook:{count+1}] Post data keys persisted: {list(post_data.keys())} | Firestore doc path: facebook_posts/{company_id}/posts/{post_id}"
                )
        
                logger.info(f"✅ Generated Facebook post {count+1}/{facebook_post_count} with ID: {post_id}")

            except Exception as e:
                logger.error(f"Failed to generate Facebook post {count+1}: {str(e)}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Couldn't generate Facebook post number {count+1} for company {company_id}: {str(e)}")

        linkedin_posts = []
        # generate linkedin posts
        for count in range(linkedin_post_count):
            try:
                logger.info(f"Generating LinkedIn post {count+1}")
                logger.debug(f"[LinkedIn:{count+1}] Calling planner with payload: {planner_request.dict()}")
                
                # FIX: Pass the Pydantic model
                planner = await generate_linkedin_planner(planner_request, company_id)
                if not planner:
                    raise Exception("Planner returned None")
                
                # generate image for post
                image_prompt = planner.get('image_prompt')
                if not image_prompt:
                    raise Exception("No image prompt returned from planner")
                
                # Create proper ContentRequest
                content_request = ContentRequest(image_prompt=image_prompt)
                logger.debug(
                    f"[LinkedIn:{count+1}] Image prompt preview: {image_prompt[:120]}{'...' if len(image_prompt) > 120 else ''}"
                )
                image_result = await generate_image_linkedin(content_request, company_id)
                image_url = image_result.get('image_url')
                
                if not image_url:
                    raise Exception("No image URL returned from image generation")
                
                # save post to db
            
                
                db = get_firestore_client()
                logger.debug(f"[LinkedIn:{count+1}] Firestore client initialized for company {company_id}")
                post_data = {
                    "company_id": company_id,
                    "channel": "linkedin",  
                    "image_url": image_url,
                    "caption": planner.get('caption', ''),
                    "hashtags": planner.get('hashtags', []),
                    "status" : "draft",
                    "overlay_text": planner.get('overlay_text', ''),
                    "scheduled_month": scheduled_month,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }

                doc_ref = db.collection('linkedin_posts').document(company_id).collection('posts').add(post_data)
                post_id = doc_ref[1].id
                linkedin_posts.append(post_id)
                logger.debug(
                    f"[LinkedIn:{count+1}] Post data keys persisted: {list(post_data.keys())} | Firestore doc path: linkedin_posts/{company_id}/posts/{post_id}"
                )
                
                logger.info(f"✅ Generated LinkedIn post {count+1}/{linkedin_post_count} with ID: {post_id}")

            except Exception as e:
                logger.error(f"Failed to generate LinkedIn post {count+1}: {str(e)}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Couldn't generate LinkedIn post number {count+1} for company {company_id}: {str(e)}")
            
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