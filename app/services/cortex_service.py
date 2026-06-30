import os
import threading
import requests
from app.utils.response_parser import parse_response
from app.utils import job_store

AGENT_API_KEY = os.getenv("AGENT_API_KEY")
AGENT_API_URL = os.getenv("AGENT_API_URL")


def call_cortex(question: str, thread_id=None, parent_message_id=None):
    """Synchronous Cortex call. Existing behaviour unchanged; thread params optional."""
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

    # --- NEW: threading. Only added when we have a thread; otherwise ask Cortex to create one. ---
    if thread_id is not None and parent_message_id is not None:
        payload["thread_id"] = thread_id
        payload["parent_message_id"] = parent_message_id
    else:
        payload["create_thread_if_not_present"] = True
        payload["parent_message_id"] = 0

    response = requests.post(
        AGENT_API_URL,
        headers={
            "Authorization": f"Bearer {AGENT_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
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