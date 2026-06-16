from pydantic import BaseModel
from typing import Optional

class AskRequest(BaseModel):
    question: str
    user_email: Optional[str] = None