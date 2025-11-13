from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class CompanyRequest(BaseModel):
    company_name: Optional[str] = None
    url: Optional[str] = None
    company_info: Optional[str] = None
    address: Optional[str] = None
    favicon_url: Optional[str] = None
    font_typography: Optional[List[str]] = None
    industry: Optional[str] = None
    keywords: Optional[List[str]] = None
    logo_url: Optional[str] = None
    target_group: Optional[str] = None
    theme_colors: Optional[List[str]] = None
    tone_analysis: Optional[str] = None
    products: Optional[List[str]] = None
    matched_fonts: Optional[Dict[str, Any]] = None
    product_categories: Optional[Dict[str, Any]] = None

    
    
    


