from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timezone

class RequestModel(BaseModel):
    status : str 
    target_id: Optional[str] = None

