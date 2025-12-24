from fastapi import APIRouter, Depends, HTTPException
from models.blog_model import BlogRequest, BlogDocument, BlogScheduleRequest, BlogResponse
from services.gpt_service import generate_blog
from config.firebase_config import get_firestore_client
from google.cloud import firestore
from datetime import datetime, timezone
from uuid import uuid4
from typing import List

from utils.logger import setup_logger
from cache.redis_config import redis_set, redis_get, redis_delete, redis_list_push, redis_list_get_all, redis_list_set_all

logger = setup_logger("marketing-app")

router = APIRouter()

async def get_db():
    return get_firestore_client()


@router.post("/blog/{company_id}/generate", response_model=BlogDocument)
async def create_blog(request: BlogRequest, company_id: str, db: firestore.Client = Depends(get_db)):
    company_ref = db.collection("companies").document(company_id)
    company_doc = company_ref.get()
    if not company_doc.exists:
        raise HTTPException(status_code=404, detail="Company not found")
    company_data = company_doc.to_dict()

    blog = generate_blog(
        company_data,
        theme=request.theme,
        theme_description=request.theme_description,
        regional_language=request.regional_language,
    )

    # Generate a unique blog ID
    blog_id = uuid4().hex

    # Save blog data to Firestore:
    # channels -> blog -> companies -> {company_id} -> blogs -> {blog_id}
    now = datetime.now(timezone.utc)
    
    # Remove token_usage from the response before saving to Firestore
    blog_for_storage = blog.copy()
    blog_for_storage.pop("token_usage", None)
    
    doc_data = {
        "company_id": company_id,
        "blog_id": blog_id,
        "created_at": now,
        "updated_at": now,
        "status": "scheduled",
        "response": blog_for_storage,
    }

    doc_ref = (
        db.collection("channels")
        .document("blog")
        .collection("companies")
        .document(company_id)
        .collection("blogs")
        .document(blog_id)
    )
    doc_ref.set(doc_data)

    return BlogDocument(
        blog_id=blog_id,
        company_id=company_id,
        created_at=now,
        updated_at=now,
        scheduled_time=None,
        scheduled_datetime=None,
        status="scheduled",
        response=BlogResponse(**blog),
    )


@router.get("/blogs/{company_id}", response_model=List[BlogDocument])
async def get_blogs_by_company_id(
    company_id: str, db: firestore.Client = Depends(get_db)
    ):
    """
    Return all blogs generated for a given company_id.
    """
    # Try to get from cache first
    cached_data = await redis_list_get_all(f"blog_posts_{company_id}")
    if cached_data:
        logger.info(f"✅ Blogs fetched from redis successfully for company {company_id} (count: {len(cached_data)})")
        # Convert cached dictionaries to BlogDocument objects
        results: List[BlogDocument] = []
        for data in cached_data:
            # Handle both dict and already-parsed data
            if isinstance(data, dict):
                response_data = data.get("response")
                if not response_data:
                    logger.warning(f"Skipping blog with missing response: {data.get('blog_id')}")
                    continue
                try:
                    # Handle case where response_data might already be a BlogResponse object
                    if isinstance(response_data, BlogResponse):
                        response_obj = response_data
                    elif isinstance(response_data, dict):
                        response_obj = BlogResponse(**response_data)
                    else:
                        # Convert to dict if it's some other type
                        response_obj = BlogResponse(**dict(response_data))
                    
                    # Parse datetime strings back to datetime objects
                    created_at = data.get("created_at")
                    if isinstance(created_at, str):
                        try:
                            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        except (ValueError, AttributeError):
                            created_at = datetime.fromisoformat(created_at)
                    
                    updated_at = data.get("updated_at")
                    if isinstance(updated_at, str):
                        try:
                            updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                        except (ValueError, AttributeError):
                            updated_at = datetime.fromisoformat(updated_at)
                    
                    scheduled_time = data.get("scheduled_time")
                    if scheduled_time and isinstance(scheduled_time, str):
                        try:
                            scheduled_time = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
                        except (ValueError, AttributeError):
                            scheduled_time = datetime.fromisoformat(scheduled_time)
                    
                    results.append(
                        BlogDocument(
                            blog_id=data.get("blog_id"),
                            company_id=data.get("company_id"),
                            created_at=created_at,
                            updated_at=updated_at,
                            scheduled_time=data.get("scheduled_time"),
                            scheduled_datetime=data.get("scheduled_datetime"),
                            status=data.get("status", "scheduled"),
                            month_id=data.get("month_id", None),
                            response=response_obj,
                        )
                    )
                except Exception as e:
                    # Skip malformed records instead of failing the whole request
                    logger.warning(f"Skipping malformed blog {data.get('blog_id')}: {str(e)}")
                    continue
        logger.info(f"✅ Converted {len(results)} blogs from cache for company {company_id}")
        return results
    else:
        logger.info(f"❌ Blogs not found in redis for company {company_id}, fetching from DB")

    blogs_ref = (
        db.collection("channels")
        .document("blog")
        .collection("companies")
        .document(company_id)
        .collection("blogs")
    )

    docs = blogs_ref.stream()

    results: List[BlogDocument] = []
    for doc in docs:
        data = doc.to_dict() or {}
        response_data = data.get("response")
        if not response_data:
            continue
        try:
            # Handle case where response_data might already be a BlogResponse object
            if isinstance(response_data, BlogResponse):
                response_obj = response_data
            elif isinstance(response_data, dict):
                response_obj = BlogResponse(**response_data)
            else:
                # Convert to dict if it's some other type
                response_obj = BlogResponse(**dict(response_data))
            
            results.append(
                BlogDocument(
                    blog_id=data.get("blog_id"),
                    company_id=data.get("company_id"),
                    created_at=data.get("created_at"),
                    updated_at=data.get("updated_at"),
                    scheduled_time=data.get("scheduled_time", None),
                    scheduled_datetime=data.get("scheduled_datetime", None),
                    status=data.get("status", "scheduled"),
                    month_id=data.get("month_id", None),
                    response=response_obj,
                )
            )
        except Exception as e:
            # Skip malformed records instead of failing the whole request
            logger.warning(f"Skipping malformed blog {data.get('blog_id')}: {str(e)}")
            continue
    # Save blogs to redis - convert Pydantic models to dicts first
    blogs_dicts = [blog.model_dump() for blog in results]
    if await redis_list_set_all(f"blog_posts_{company_id}", blogs_dicts):
        logger.info(f"✅ Blogs saved to redis successfully for company {company_id} (count: {len(blogs_dicts)})")
    else:
        logger.warning(f"⚠️ Failed to save blogs to redis for company {company_id}, continuing anyway")
    return results


@router.get("/blogs/{company_id}/{blog_id}", response_model=BlogDocument)
async def get_blog_by_id(
    company_id: str, blog_id: str, db: firestore.Client = Depends(get_db)
    ):


    doc_ref = (
        db.collection("channels")
        .document("blog")
        .collection("companies")
        .document(company_id)
        .collection("blogs")
        .document(blog_id)
    )
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Blog not found")

    data = doc.to_dict() or {}
    response_data = data.get("response")
    if not response_data:
        raise HTTPException(status_code=500, detail="Blog data missing in document")

    # Handle case where response_data might already be a BlogResponse object
    if isinstance(response_data, BlogResponse):
        response_obj = response_data
    elif isinstance(response_data, dict):
        response_obj = BlogResponse(**response_data)
    else:
        # Convert to dict if it's some other type
        response_obj = BlogResponse(**dict(response_data))

    return BlogDocument(
        blog_id=data.get("blog_id"),
        company_id=data.get("company_id"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
        scheduled_time=data.get("scheduled_time", None),
        scheduled_datetime=data.get("scheduled_datetime", None),
        status=data.get("status", "scheduled"),
        month_id=data.get("month_id"),
        response=response_obj,
    )


@router.put("/blogs/{company_id}/{blog_id}/schedule", response_model=BlogDocument)
async def schedule_blog(
    company_id: str,
    blog_id: str,
    payload: BlogScheduleRequest,
    db: firestore.Client = Depends(get_db),
    ):

    doc_ref = (
        db.collection("channels")
        .document("blog")
        .collection("companies")
        .document(company_id)
        .collection("blogs")
        .document(blog_id)
    )
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Blog not found")

    now = datetime.now(timezone.utc)
    schedule_dt = datetime.fromisoformat(payload.scheduled_time.replace('Z', '+00:00'))

    doc_ref.update(
        {
            "scheduled_time": payload.scheduled_time,
            "scheduled_datetime": schedule_dt,
            "status": "scheduled",
            "updated_at": firestore.SERVER_TIMESTAMP,
            "month_id": payload.month_id,
        }
    )

    updated = doc_ref.get().to_dict() or {}
    response_data = updated.get("response")
    if not response_data:
        raise HTTPException(status_code=500, detail="Blog data missing in document")

    # Handle case where response_data might already be a BlogResponse object
    if isinstance(response_data, BlogResponse):
        response_obj = response_data
    elif isinstance(response_data, dict):
        response_obj = BlogResponse(**response_data)
    else:
        # Convert to dict if it's some other type
        response_obj = BlogResponse(**dict(response_data))

    #invalidate cache
    if await redis_delete(f"blog_posts_{company_id}"):
        logger.info(f"✅ Blog posts cache invalidated for company {company_id}")
    else:
        logger.warning(f"⚠️ Failed to invalidate Blog posts cache for company {company_id}")

    return BlogDocument(
        blog_id=updated.get("blog_id"),
        company_id=updated.get("company_id"),
        created_at=updated.get("created_at"),
        updated_at=updated.get("updated_at"),
        scheduled_time=updated.get("scheduled_time"),
        scheduled_datetime=updated.get("scheduled_datetime"),
        status=updated.get("status", "scheduled"),
        month_id=updated.get("month_id"),
        response=response_obj,
    )

