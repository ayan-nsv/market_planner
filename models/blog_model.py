from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class BlogSection(BaseModel):
    heading: str
    content: str


class BlogRequest(BaseModel):
    theme: str
    theme_description: str
    regional_language: Optional[str] = None



class BlogResponse(BaseModel):
    title: str
    meta_description: str
    introduction: str
    sections: List[BlogSection]
    conclusion: str
    call_to_action: str


class BlogDocument(BaseModel):
    blog_id: str
    company_id: str
    created_at: datetime
    updated_at: datetime
    scheduled_time: Optional[str] = None
    scheduled_datetime: Optional[datetime] = None
    status: str = "scheduled"
    month_id: Optional[int] = None
    response: BlogResponse


class BlogScheduleRequest(BaseModel):
    scheduled_time: str
    month_id: Optional[int] = None