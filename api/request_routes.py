from fastapi import APIRouter, HTTPException
from grpc import StatusCode
from models.request_model import RequestModel
from google.cloud import firestore
from config.firebase_config import get_firestore_client
from utils.logger import setup_logger


logger = setup_logger("marketing-app")
router = APIRouter()
db = get_firestore_client()

@router.post("/request/{sernder_id}/{target_id}")
def generate_request(target_id: str, sender_id: str):
    try:
        reciever_ref = db.collection("users").document(target_id)
        reciever = reciever_ref.get()

        if not reciever.exists:
            logger.error(f"     reciever user doesnt exist!!")
            raise HTTPException(status_code=404, detail=f"Reciever user doesnt exist!!")
        

        final_data = {
                        "status": "pending",
                        "sender" : sender_id,
                        "receiver" : target_id,
                        "created_at": firestore.SERVER_TIMESTAMP,
                        "updated_at": firestore.SERVER_TIMESTAMP  
                     }
        
        logger.info(f"  Sending invitation request to {target_id}")
        doc_ref = db.collection("requests").document(target_id).collection("list").add(final_data)

        logger.info(f"      Invitation request sent to {target_id}")

        return {
                    "status": "pending",
                    "sender" : sender_id,
                    "receiver" : target_id,
                    "id": doc_ref[1].id
                }
    except Exception as e:
        logger.error(f"     coudnt sent a request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/request/{request_id}")
def update_request(request_id: str, request: RequestModel):
    try:
        request_ref= db.collection("requests").document(request.target_id).collection("list").document(request_id)
        request_snapshot = request_ref.get()

        if not request_snapshot.exists:
            logger.error(f"  Request doesn't exixts")
            raise HTTPException(status_code=404, detail=f"  Request doesn't exixts")
        
        update_data = request.model_dump(exclude_unset=True)
        update_data["updated_at"] = firestore.SERVER_TIMESTAMP

        if update_data:
            request_ref.update(update_data)
            return {
                "status": "success", 
                "message": f"request {request_id} updated",
                "updated_fields": list(update_data.keys())
            }
        else:
            return {"status": "success", "message": "No fields to update"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"     coudn't update the request!")
        raise HTTPException(status_code=500, detail=f"Error updating post: {str(e)}")
    
   
        