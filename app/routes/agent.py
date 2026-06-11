from fastapi import APIRouter

from app.models.request_models import AskRequest
from app.services.cortex_service import call_cortex

router = APIRouter()


@router.post("/ask")
async def ask_agent(request: AskRequest):

    return call_cortex(request.question)