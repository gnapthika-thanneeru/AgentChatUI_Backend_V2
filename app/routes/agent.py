from fastapi import APIRouter
from app.models.request_models import AskRequest
from app.services.cortex_service import call_cortex, start_async_job
from app.utils import job_store

router = APIRouter()

# POC allowlist — lowercase. Add up to 10-15 emails here.
ALLOWED_EMAILS = {
    "xrsm@novonordisk.com",
    "okua@novonordisk.com",
    "zukm@novonordisk.com",
    "ugtw@novonordisk.com",
    "setn@novonordisk.com",
    "sjmn@novonordisk.com",
    "sgxq@novonordisk.com",
    "skbt@novonordisk.com",
    "lkqq@novonordisk.com",
    "wrak@novonordisk.com",
    "wpvm@novonordisk.com",
    "wkom@novonordisk.com",
    "vhpt@novonordisk.com",
    "psie@novonordisk.com",
    "frka@novonordisk.com",
}
POC_DENIED_MESSAGE = "This assistant is available for POC users only. Please contact the project team for access."


# ---- ORIGINAL endpoint, UNCHANGED (kept as fallback) ----
@router.post("/ask")
async def ask_agent(request: AskRequest):
    email = (request.user_email or "").strip().lower()
    if email not in ALLOWED_EMAILS:
        return {"answer": POC_DENIED_MESSAGE}
    return call_cortex(request.question)


# ---- NEW: start an async job, return job_id immediately ----
@router.post("/ask-async")
async def ask_agent_async(request: AskRequest):
    email = (request.user_email or "").strip().lower()
    if email not in ALLOWED_EMAILS:
        # Same allowlist behaviour; return denied as an immediately-complete result shape.
        return {"status": "done", "result": {"answer": POC_DENIED_MESSAGE}}
    job_id = start_async_job(request.question)
    return {"status": "pending", "job_id": job_id}


# ---- NEW: poll job status/result ----
@router.get("/status/{job_id}")
async def get_status(job_id: str):
    job = job_store.get_job(job_id)
    if not job:
        return {"status": "not_found"}
    if job["status"] == "pending":
        return {"status": "pending"}
    if job["status"] == "error":
        return {"status": "error", "error": job["error"]}
    return {"status": "done", "result": job["result"]}
