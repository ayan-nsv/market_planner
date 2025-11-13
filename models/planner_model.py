from pydantic import BaseModel
from typing import List, Optional

class PlannerRequest(BaseModel):
    theme_title: Optional[str] = None
    theme_description: Optional[str] = None
    
