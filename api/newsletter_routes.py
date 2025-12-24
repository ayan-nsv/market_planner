from fastapi import APIRouter, Depends, HTTPException
from models.newsletter_model import NewsletterRequest, NewsletterDocument, NewsletterScheduleRequest, NewsletterResponse
from services.gpt_service import generate_newsletter
from config.firebase_config import get_firestore_client
from google.cloud import firestore
from datetime import datetime, timezone
from uuid import uuid4
from typing import List
from cache.redis_config import redis_delete, redis_list_get_all, redis_list_set_all
from utils.logger import setup_logger

logger = setup_logger("marketing-app")

async def get_db():
    return get_firestore_client()

router = APIRouter()


@router.post("/newsletter/{company_id}/generate", response_model=NewsletterDocument)
async def create_newsletter(request: NewsletterRequest, company_id: str, db: firestore.Client = Depends(get_db)):
    company_ref = db.collection("companies").document(company_id)
    company_doc = company_ref.get()
    if not company_doc.exists:
        raise HTTPException(status_code=404, detail="Company not found")
    company_data = company_doc.to_dict()
    newsletter = generate_newsletter(
        company_data,
        request.theme,
        request.theme_description,
        request.regional_language
    )

    # Generate a unique newsletter ID
    newsletter_id = uuid4().hex

    # Remove token_usage from the response before saving to Firestore
    newsletter_for_storage = newsletter.copy()
    newsletter_for_storage.pop("token_usage", None)
    
    doc_data = {
        "company_id": company_id,
        "newsletter_id": newsletter_id,
        "created_at": firestore.SERVER_TIMESTAMP,
        "updated_at": firestore.SERVER_TIMESTAMP,
        "status": "draft",
        "response": newsletter_for_storage,
    }

    # Save newsletter data to Firestore:
    # channels -> newsletter -> companies -> {company_id} -> newsletters -> {newsletter_id}
    doc_ref = (
        db.collection("channels")
        .document("newsletter")
        .collection("companies")
        .document(company_id)
        .collection("newsletters")
        .document(newsletter_id)
    )
    doc_ref.set(doc_data)

    # Use current datetime for the response since SERVER_TIMESTAMP is only for Firestore
    current_time = datetime.now(timezone.utc)
    return NewsletterDocument(
        newsletter_id=newsletter_id,
        company_id=company_id,
        created_at=current_time,
        updated_at=current_time,
        scheduled_time=None,
        scheduled_datetime=None,
        status="draft",
        month_id=None,
        response=NewsletterResponse(**newsletter),
    )


@router.get("/newsletters/{company_id}", response_model=List[NewsletterDocument])
async def get_newsletters_by_company_id(
    company_id: str, db: firestore.Client = Depends(get_db)
    ):
    """
    Return all newsletters generated for a given company_id.
    """
    # Try to get from cache first
    cached_data = await redis_list_get_all(f"newsletter_posts_{company_id}")
    if cached_data:
        logger.info(f"✅ Newsletters fetched from redis successfully for company {company_id} (count: {len(cached_data)})")
        # Convert cached dictionaries to NewsletterDocument objects
        results: List[NewsletterDocument] = []
        for data in cached_data:
            # Handle both dict and already-parsed data
            if isinstance(data, dict):
                response_data = data.get("response")
                if not response_data:
                    logger.warning(f"Skipping newsletter with missing response: {data.get('newsletter_id')}")
                    continue
                try:
                    # Handle case where response_data might already be a NewsletterResponse object
                    if isinstance(response_data, NewsletterResponse):
                        response_obj = response_data
                    elif isinstance(response_data, dict):
                        response_obj = NewsletterResponse(**response_data)
                    else:
                        # Convert to dict if it's some other type
                        response_obj = NewsletterResponse(**dict(response_data))
                    
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
                        NewsletterDocument(
                            newsletter_id=data.get("newsletter_id"),
                            company_id=company_id,
                            created_at=created_at,
                            updated_at=updated_at,
                            status=data.get("status", "draft"),
                            scheduled_time=data.get("scheduled_time", None),
                            scheduled_datetime=data.get("scheduled_datetime", None),
                            month_id=data.get("month_id", None),
                            response=response_obj,
                        )
                    )
                except Exception as e:
                    # Skip malformed records instead of failing the whole request
                    logger.warning(f"Skipping malformed newsletter {data.get('newsletter_id')}: {str(e)}")
                    continue
        logger.info(f"✅ Converted {len(results)} newsletters from cache for company {company_id}")
        return results
    else:
        logger.info(f"❌ Newsletters not found in redis for company {company_id}, fetching from DB")

    newsletters_ref = (
        db.collection("channels")
        .document("newsletter")
        .collection("companies")
        .document(company_id)
        .collection("newsletters")
    )

    docs = newsletters_ref.stream()

    results: List[NewsletterDocument] = []
    for doc in docs:
        data = doc.to_dict() or {}
        response_data = data.get("response")
        if not response_data:
            continue
        try:
            # Handle case where response_data might already be a NewsletterResponse object
            if isinstance(response_data, NewsletterResponse):
                response_obj = response_data
            elif isinstance(response_data, dict):
                response_obj = NewsletterResponse(**response_data)
            else:
                # Convert to dict if it's some other type
                response_obj = NewsletterResponse(**dict(response_data))
            
            results.append(
                NewsletterDocument(
                    newsletter_id=data.get("newsletter_id"),
                    company_id=company_id,
                    created_at=data.get("created_at"),
                    updated_at=data.get("updated_at"),
                    scheduled_time=data.get("scheduled_time", None),
                    scheduled_datetime=data.get("scheduled_datetime", None),
                    status=data.get("status", "draft"),
                    month_id=data.get("month_id", None),
                    response=response_obj,
                )
            )
        except Exception as e:
            # Skip malformed records instead of failing the whole request
            logger.warning(f"Skipping malformed newsletter {data.get('newsletter_id')}: {str(e)}")
            continue
    # Save newsletters to redis - convert Pydantic models to dicts first
    newsletters_dicts = [newsletter.model_dump() for newsletter in results]
    if await redis_list_set_all(f"newsletter_posts_{company_id}", newsletters_dicts):
        logger.info(f"✅ Newsletters saved to redis successfully for company {company_id} (count: {len(newsletters_dicts)})")
    else:
        logger.warning(f"⚠️ Failed to save newsletters to redis for company {company_id}, continuing anyway")
    return results


@router.get("/newsletters/{company_id}/{newsletter_id}", response_model=NewsletterDocument)
async def get_newsletter_by_id(
    company_id: str, newsletter_id: str, db: firestore.Client = Depends(get_db)
    ):
    """
    Fetch a single newsletter by company_id and newsletter_id.
    """
    # Try to get from cache first
    doc_ref = (
        db.collection("channels")
        .document("newsletter")
        .collection("companies")
        .document(company_id)
        .collection("newsletters")
        .document(newsletter_id)
    )
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Newsletter not found")

    data = doc.to_dict() or {}
    response_data = data.get("response")
    if not response_data:
        raise HTTPException(
            status_code=500, detail="Newsletter data missing in document"
        )

    # Handle case where response_data might already be a NewsletterResponse object
    if isinstance(response_data, NewsletterResponse):
        response_obj = response_data
    elif isinstance(response_data, dict):
        response_obj = NewsletterResponse(**response_data)
    else:
        # Convert to dict if it's some other type
        response_obj = NewsletterResponse(**dict(response_data))

    
    return NewsletterDocument(
        newsletter_id=data.get("newsletter_id"),
        company_id=company_id,
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
        scheduled_time=data.get("scheduled_time", None),
        scheduled_datetime=data.get("scheduled_datetime", None),
        status=data.get("status", "draft"),
        month_id=data.get("month_id", None),
        response=response_obj,
    )


@router.put("/newsletters/{company_id}/{newsletter_id}/schedule",response_model=NewsletterDocument)
async def schedule_newsletter(
    company_id: str,
    newsletter_id: str,
    payload: NewsletterScheduleRequest,
    db: firestore.Client = Depends(get_db)
    ):

    doc_ref = (
        db.collection("channels")
        .document("newsletter")
        .collection("companies")
        .document(company_id)
        .collection("newsletters")
        .document(newsletter_id)
    )
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Newsletter not found")

    
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
        raise HTTPException(
            status_code=500, detail="Newsletter data missing in document"
        )

    # Handle case where response_data might already be a NewsletterResponse object
    if isinstance(response_data, NewsletterResponse):
        response_obj = response_data
    elif isinstance(response_data, dict):
        response_obj = NewsletterResponse(**response_data)
    else:
        # Convert to dict if it's some other type
        response_obj = NewsletterResponse(**dict(response_data))

    #invalidate cache
    if await redis_delete(f"newsletter_posts_{company_id}"):
        logger.info(f"✅ Newsletter posts cache invalidated for company {company_id}")
    else:
        logger.warning(f"⚠️ Failed to invalidate Newsletter posts cache for company {company_id}")

    return NewsletterDocument(
        newsletter_id=updated.get("newsletter_id"),
        company_id=company_id,
        created_at=updated.get("created_at"),
        updated_at=updated.get("updated_at"),
        scheduled_time=updated.get("scheduled_time", None),
        scheduled_datetime=updated.get("scheduled_datetime", None),
        status=updated.get("status", "scheduled"),
        month_id=updated.get("month_id", None),
        response=response_obj,
    )