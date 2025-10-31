from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ThemeRequest(BaseModel):
    month: str
    themes: List[str]
    companyId: str
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
