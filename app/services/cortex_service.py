import os
import threading
import requests
from app.utils.response_parser import parse_response
from app.utils import job_store

AGENT_API_KEY = os.getenv("AGENT_API_KEY")
AGENT_API_URL = os.getenv("AGENT_API_URL")

# Derive the threads endpoint from the account host in AGENT_API_URL.
# AGENT_API_URL example:
#   https://<account>.snowflakecomputing.com/api/v2/databases/.../agents/TEST:run
# Threads endpoint (per docs): https://<account>.snowflakecomputing.com/api/v2/cortex/threads
def _threads_url():
    if not AGENT_API_URL:
        return None
    # take everything up to "/api/" and append the cortex threads path
    base = AGENT_API_URL.split("/api/")[0]
    return f"{base}/api/v2/cortex/threads"


def _auth_headers():
    return {
        "Authorization": f"Bearer {AGENT_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def create_thread():
    """Create a new Cortex thread and return its thread_id (int) or None on failure.
    Per Snowflake docs: POST /api/v2/cortex/threads -> {"thread_id": ...}."""
    url = _threads_url()
    if not url:
        return None
    try:
        resp = requests.post(
            url,
            headers=_auth_headers(),
            json={"origin_application": "powerbi_agent_chat"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("thread_id")
    except Exception:
        # Non-fatal: if thread creation fails, we fall back to a stateless call.
        return None


def call_cortex(question: str, thread_id=None, parent_message_id=None):
    """Synchronous Cortex call. Existing behaviour preserved.
    Threading is additive: if we have a thread_id we continue it; if not, we
    create one; if creation fails, we send a normal (stateless) request exactly
    like before."""
    if not AGENT_API_KEY:
        raise ValueError("AGENT_API_KEY not configured")
    if not AGENT_API_URL:
        raise ValueError("AGENT_API_URL not configured")

    payload = {
        "stream": False,
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": question}]}
        ],
    }

    # --- Threading (additive, doc-compliant) ---
    if thread_id is not None and parent_message_id is not None:
        # Continuing an existing conversation.
        payload["thread_id"] = thread_id
        payload["parent_message_id"] = parent_message_id
    else:
        # First turn: create a thread, then start it with parent_message_id = 0.
        new_thread_id = create_thread()
        if new_thread_id is not None:
            payload["thread_id"] = new_thread_id
            payload["parent_message_id"] = 0
        # If thread creation failed, we send NO thread fields -> behaves exactly
        # like the original stateless implementation (no regression).

    response = requests.post(
        AGENT_API_URL,
        headers=_auth_headers(),
        json=payload,
        timeout=600,
    )
    response.raise_for_status()
    data = response.json()
    return parse_response(data)


def _run_job(job_id: str, question: str, thread_id=None, parent_message_id=None):
    try:
        result = call_cortex(question, thread_id, parent_message_id)
        job_store.set_done(job_id, result)
    except Exception as e:
        job_store.set_error(job_id, str(e))


def start_async_job(question: str, thread_id=None, parent_message_id=None) -> str:
    job_id = job_store.create_job()
    t = threading.Thread(
        target=_run_job,
        args=(job_id, question, thread_id, parent_message_id),
        daemon=True,
    )
    t.start()
    return job_id