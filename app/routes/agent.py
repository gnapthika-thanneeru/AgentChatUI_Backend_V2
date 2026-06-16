from fastapi import APIRouter

from app.models.request_models import AskRequest
from app.services.cortex_service import call_cortex

router = APIRouter()

# POC allowlist — lowercase. Add up to 10–15 emails here.
ALLOWED_EMAILS = {
    "okua@novonordisk.com",
    "ugtw@novonordisk.com",
    "zukm@novonordisk.com"
}

POC_DENIED_MESSAGE = "This assistant is available for POC users only. Please contact the project team for access."


@router.post("/ask")
async def ask_agent(request: AskRequest):

    email = (request.user_email or "").strip().lower()

    if email not in ALLOWED_EMAILS:
        return {"answer": POC_DENIED_MESSAGE}

    return call_cortex(request.question)