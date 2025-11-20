from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# Each Pydantic model below maps to a MongoDB collection (lowercased class name)

class ContactMessage(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    phone: str = Field(..., min_length=6, max_length=40)
    email: Optional[EmailStr] = None
    message: str = Field(..., min_length=5, max_length=4000)
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    source: str = "website"
