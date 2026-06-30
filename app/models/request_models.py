from pydantic import BaseModel
from typing import Optional

class AskRequest(BaseModel):
    question: str
    user_email: Optional[str] = None
    thread_id: Optional[int] = None 
    parent_message_id: Optional[int] = None