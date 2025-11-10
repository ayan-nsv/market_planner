from pydantic import BaseModel
from typing import Optional

class SchedularRequest(BaseModel):
    theme: Optional[str] = None
    theme_description: Optional[str] = None
    scheduled_month: Optional[int] = None
    instagram_post_count: Optional[int] = None
    facebook_post_count: Optional[int] = None
    linkedin_post_count: Optional[int] = None
 