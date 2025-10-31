from pydantic import BaseModel
from typing import List, Optional

class PlannerRequest(BaseModel):
    theme_title: Optional[str] = None
    theme_description: Optional[str] = None


class PlannerUpdateRequest(BaseModel):
    channel: Optional[str] = None
    image_prompt: Optional[str] = None
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None
    overlay_text: Optional[str] = None