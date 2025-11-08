
from datetime import datetime, timezone
from google.cloud import firestore
from config.firebase_config import get_firestore_client
from services.content_service import generate_scheduled_posts

from google.cloud.firestore_v1 import FieldFilter

from utils.logger import setup_logger
logger = setup_logger("marketing-app")

# async def process_due_posts():
#     db = get_firestore_client()
#     now = datetime.now(timezone.utc)

#     logger.info("🚀 Starting scheduled post processing at %s", now.isoformat())

#     processed_count = 0
#     skipped_count = 0
#     failed_count = 0

#     try:
#         # Get all company documents in "scheduled_posts"
#         companies = db.collection("scheduled_posts").stream()

#         for company_doc in companies:
#             company_id = company_doc.id
#             logger.info("Checking posts for company %s", company_id)

#             # Get all pending posts within this company’s posts subcollection
#             posts_ref = (
#                 company_doc.reference.collection("posts")
#                 .where(filter=FieldFilter("status", "==", "pending"))
#                 .where(filter=FieldFilter("scheduled_at", "<=", datetime.now(timezone.utc)))
#             )

#             posts = list(posts_ref.stream())
#             logger.info("Found %d pending posts for company %s", len(posts), company_id)

#             for doc in posts:
#                 data = doc.to_dict()
#                 ref = doc.reference

#                 logger.info(
#                     "Processing post %s for company %s (scheduled_at=%s)",
#                     doc.id,
#                     company_id,
#                     data.get("scheduled_at"),
#                 )

#                 ref.update({
#                     "status": "processing",
#                     "updated_at": firestore.SERVER_TIMESTAMP,
#                 })

#                 try:
#                     response =  generate_scheduled_posts(company_id, data.get("post_data", {}))
#                     ref.update({
#                         "status": "completed",
#                         "completed_at": firestore.SERVER_TIMESTAMP,
#                         "generated_post_ids": response.get("post_ids", [])
#                     })
#                     processed_count += 1
#                     logger.info(
#                         "✅ Completed post %s for company %s",
#                         doc.id,
#                         company_id,
#                     )

#                 except Exception as exc:
#                     failed_count += 1
#                     ref.update({
#                         "status": "failed",
#                         "error": str(exc),
#                         "updated_at": firestore.SERVER_TIMESTAMP,
#                     })
#                     logger.error(
#                         "❌ Failed to process post %s for company %s: %s",
#                         doc.id,
#                         company_id,
#                         str(exc),
#                         exc_info=True,
#                     )

#         logger.info(
#             "🎯 Finished processing posts — Completed: %d | Failed: %d | Skipped: %d",
#             processed_count,
#             failed_count,
#             skipped_count,
#         )

#     except Exception as e:
#         logger.exception("⚠️ Error while processing due posts: %s", str(e))



async def process_due_posts():
    db = get_firestore_client()
    now = datetime.now(timezone.utc)

    logger.info("🚀 Starting scheduled post processing at %s", now.isoformat())

    processed_count = 0
    skipped_count = 0
    failed_count = 0

    try:
        # Get all company documents in "scheduled_posts"
        companies = db.collection("scheduled_posts").stream()

        for company_doc in companies:
            company_id = company_doc.id
            logger.info("Checking posts for company %s", company_id)

            # FIXED: Query for posts that are scheduled for now or in the past AND are pending
            posts_ref = (
                company_doc.reference.collection("posts")
                .where(filter=FieldFilter("status", "==", "pending"))
                .where(filter=FieldFilter("scheduled_at", "<=", now))
            )

            # Execute query and convert to list
            posts = list(posts_ref.stream())
            logger.info("Found %d due posts for company %s", len(posts), company_id)

            if not posts:
                logger.info("No due posts found for company %s", company_id)
                continue

            for doc in posts:
                data = doc.to_dict()
                ref = doc.reference

                logger.info(
                    "Processing post %s for company %s (scheduled_at=%s, now=%s)",
                    doc.id,
                    company_id,
                    data.get("scheduled_at"),
                    now.isoformat()
                )

                # Update status to processing
                ref.update({
                    "status": "processing",
                    "updated_at": firestore.SERVER_TIMESTAMP,
                })

                try:
                    # Fix: Pass the correct field names to content service
                    post_data_for_content = {
                        **data.get("post_data", {}),
                        "scheduled_time": data.get("scheduled_date"),  # Map scheduled_date to scheduled_time
                        "company_id": company_id
                    }
                    
                    response = generate_scheduled_posts(company_id, post_data_for_content)
                    
                    ref.update({
                        "status": "completed",
                        "completed_at": firestore.SERVER_TIMESTAMP,
                        "generated_post_ids": response.get("post_ids", [])
                    })
                    processed_count += 1
                    logger.info(
                        "✅ Completed post %s for company %s, generated %d posts",
                        doc.id,
                        company_id,
                        len(response.get("post_ids", []))
                    )

                except Exception as exc:
                    failed_count += 1
                    ref.update({
                        "status": "failed",
                        "error": str(exc),
                        "updated_at": firestore.SERVER_TIMESTAMP,
                    })
                    logger.error(
                        "❌ Failed to process post %s for company %s: %s",
                        doc.id,
                        company_id,
                        str(exc),
                        exc_info=True,
                    )

        logger.info(
            "🎯 Finished processing posts — Completed: %d | Failed: %d | Skipped: %d",
            processed_count,
            failed_count,
            skipped_count,
        )

    except Exception as e:
        logger.exception("⚠️ Error while processing due posts: %s", str(e))