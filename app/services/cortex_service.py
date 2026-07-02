import os
import threading
import requests
from app.utils.response_parser import parse_response
from app.utils import job_store

AGENT_API_KEY = os.getenv("AGENT_API_KEY")
AGENT_API_URL = os.getenv("AGENT_API_URL")


def _threads_url():
    if not AGENT_API_URL:
        return None
    base = AGENT_API_URL.split("/api/")[0]
    return f"{base}/api/v2/cortex/threads"


def _auth_headers():
    return {
        "Authorization": f"Bearer {AGENT_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def create_thread():
    """Create a new Cortex thread and return its thread_id (int) or None on failure."""
    url = _threads_url()
    print(f"[THREAD] URL: {url}", flush=True)
    if not url:
        print("[THREAD] No URL built", flush=True)
        return None
    try:
        resp = requests.post(
            url,
            headers=_auth_headers(),
            json={"origin_application": "powerbi_agent_chat"},
            timeout=30,
        )
        print(f"[THREAD] status={resp.status_code} body={resp.text}", flush=True)
        resp.raise_for_status()
        thread_id = resp.json().get("thread_id")
        print(f"[THREAD] thread_id={thread_id}", flush=True)
        return thread_id
    except Exception as e:
        print(f"[THREAD] FAILED: {e}", flush=True)
        return None


def call_cortex(question: str, thread_id=None, parent_message_id=None):
    """Synchronous Cortex call. Existing behaviour preserved; threading additive."""
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
    if thread_id and parent_message_id is not None and thread_id != 0:
        # Continuing an existing conversation.
        payload["thread_id"] = thread_id
        payload["parent_message_id"] = parent_message_id
    else:
        # First turn: create a thread, then start it with parent_message_id = 0.
        new_thread_id = create_thread()
        if new_thread_id is not None:
            payload["thread_id"] = new_thread_id
            payload["parent_message_id"] = 0
        # If thread creation failed, send NO thread fields -> original stateless behaviour.

    print(f"[RUN] payload_keys={list(payload.keys())} thread_id={payload.get('thread_id')} parent={payload.get('parent_message_id')}", flush=True)

    response = requests.post(
        AGENT_API_URL,
        headers=_auth_headers(),
        json=payload,
        timeout=600,
    )
    response.raise_for_status()
    data = response.json()

    print(f"[RUN] response_metadata={data.get('metadata')}", flush=True)

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