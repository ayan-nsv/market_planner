
from datetime import datetime, timezone
from google.cloud import firestore
from config.firebase_config import get_firestore_client
from services.content_service import generate_scheduled_posts

from google.cloud.firestore_v1 import FieldFilter

from utils.logger import setup_logger
logger = setup_logger("marketing-app")

db = get_firestore_client()

async def process_due_posts():
    logger.info("🚀 Starting scheduled post processing")

    processed_count = 0
    skipped_count = 0
    failed_count = 0

    try:
        # ✅ Only fetch companies under scheduled_posts
        logger.info("📋 Querying scheduled_posts collection...")
        companies_query = db.collection("scheduled_posts")
        
        try:
            companies = companies_query.stream()
            companies_list = list(companies)
            logger.info("📊 Found %d company documents in scheduled_posts", len(companies_list))
        except Exception as stream_error:
            logger.error("❌ Failed to stream companies from scheduled_posts: %s", stream_error)
            raise Exception(f"Failed to read scheduled_posts collection: {str(stream_error)}")

        if not companies_list:
            logger.warning("⚠️ No company documents found in scheduled_posts collection")
            return {
                "status": "success",
                "processed": processed_count,
                "failed": failed_count,
                "skipped": skipped_count,
                "message": "No companies found in scheduled_posts collection"
            }

        for company_doc in companies_list:
            company_id = company_doc.id
            logger.info("📂 Checking company %s", company_id)

            # ✅ Only fetch posts under this company path
            try:
                posts_query = (
                    company_doc.reference.collection("posts")
                    .where("status", "==", "pending")
                )
                posts = list(posts_query.stream())
                logger.debug("🔍 Posts query executed for company %s", company_id)
            except Exception as posts_query_error:
                logger.error("❌ Failed to query posts for company %s: %s", company_id, posts_query_error)
                failed_count += 1
                continue

            if not posts:
                logger.info("➡️ No pending posts for %s", company_id)
                skipped_count += 1
                continue

            logger.info("✅ %d pending posts found for %s", len(posts), company_id)

            for post_doc in posts:
                post_id = post_doc.id
                data = post_doc.to_dict()
                ref = post_doc.reference

                logger.info("📝 Processing post %s", post_id)

                # Move status → processing
                try:
                    ref.update({
                        "status": "processing",
                        "updated_at": firestore.SERVER_TIMESTAMP
                    })
                except Exception as e:
                    logger.error("❌ Failed to mark %s as processing: %s", post_id, e)
                    failed_count += 1
                    continue

                month_id = data.get("month_id")
                post_data = data.get("post_data") or {}

                try:
                    # Prepare payload
                    payload = {
                        **post_data,
                        "company_id": company_id,
                        "scheduled_month": month_id,
                    }

                    # Call generator
                    response = await generate_scheduled_posts(company_id, payload)

                    if not response or not isinstance(response, dict):
                        raise Exception("Invalid generator response")

                    generated_ids = response.get("post_ids", [])

                    # Mark completed
                    ref.update({
                        "status": "completed",
                        "completed_at": firestore.SERVER_TIMESTAMP,
                        "generated_post_ids": generated_ids
                    })

                    processed_count += 1
                    logger.info("✅ Completed %s | generated %d posts", post_id, len(generated_ids))

                except Exception as e:
                    logger.error("❌ Process failed for %s: %s", post_id, e)
                    failed_count += 1
                    try:
                        ref.update({
                            "status": "failed",
                            "error": str(e),
                            "updated_at": firestore.SERVER_TIMESTAMP
                        })
                    except Exception as ue:
                        logger.error("❌ Failed updating error state: %s", ue)

        return {
            "status": "success",
            "processed": processed_count,
            "failed": failed_count,
            "skipped": skipped_count
        }

    except Exception as e:
        logger.exception("🔥 Fatal error in process_due_posts: %s", e)
        return {
            "status": "error",
            "error": str(e),
            "processed": processed_count,
            "failed": failed_count,
            "skipped": skipped_count
        }

