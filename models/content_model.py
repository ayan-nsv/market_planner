from typing import Optional, List
from pydantic import BaseModel, validator
from datetime import datetime, timezone

class ContentRequest(BaseModel):
    image_prompt: str

class ContentSaveRequest(BaseModel):
    image_url: Optional[str] = None
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None
    scheduled_time: Optional[str] = None

    @validator('scheduled_time')
    def validate_scheduled_time_format(cls, v):
        if v is not None:
            try:
                # Parse to check format, but return original string
                parsed_dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
                return v
            except ValueError:
                raise ValueError('scheduled_time must be in ISO format (e.g., "2024-01-15T14:30:00" or "2024-01-15T14:30:00Z")')
        return v

    @property
    def scheduled_datetime(self) -> Optional[datetime]:
        """Convert string scheduled_time to datetime object for storage"""
        if self.scheduled_time:
            try:
                return datetime.fromisoformat(self.scheduled_time.replace('Z', '+00:00'))
            except ValueError:
                return None
        return None

    def is_future_schedule(self) -> bool:
        """Check if scheduled time is in the future with timezone awareness"""
        if self.scheduled_datetime:
            # Make both datetimes timezone-aware for comparison
            scheduled_dt = self.scheduled_datetime
            
            # If scheduled_dt is timezone-aware, make now timezone-aware too
            if scheduled_dt.tzinfo is not None:
                now = datetime.now(timezone.utc)
            else:
                now = datetime.now()
            
            return scheduled_dt > now
        return False