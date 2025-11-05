from pydantic import BaseModel
from typing import List, Optional

class SchedularRequest(BaseModel):
    theme: Optional[str]
    theme_description: Optional[str]
    instagram_post_count: int
    facebook_post_count: int
    linkedin_post_count: int
    scheduled_date: str 