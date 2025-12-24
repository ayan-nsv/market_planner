from pydantic import BaseModel
from typing import Optional
from datetime import datetime




class NewsletterRequest(BaseModel):
    theme: str
    theme_description: str
    regional_language: Optional[str] = None


class NewsletterResponse(BaseModel):
    channel: str
    subject_line: str
    preheader: str
    greeting: str
    opening_paragraph: str
    main_content: str
    practical_tips_section: str
    call_to_action: str
    closing: str


class NewsletterDocument(BaseModel):
    newsletter_id: str
    company_id: str
    created_at: datetime
    updated_at: datetime
    scheduled_time: Optional[str] = None
    scheduled_datetime: Optional[datetime] = None
    status: str = "scheduled"
    month_id: Optional[int] = None
    response: NewsletterResponse


class NewsletterScheduleRequest(BaseModel):
    scheduled_time: str
    month_id: Optional[int] = None