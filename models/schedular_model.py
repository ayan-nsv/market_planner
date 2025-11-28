from pydantic import BaseModel
from typing import Optional

class SchedularRequest(BaseModel):
    theme: Optional[str] = None
    theme_description: Optional[str] = None
    scheduled_month: Optional[int] = None
    month_id: Optional[int] = None
    theme_index: Optional[int] = None
 