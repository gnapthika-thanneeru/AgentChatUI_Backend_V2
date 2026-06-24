import os
import threading
import requests
from app.utils.response_parser import parse_response
from app.utils import job_store

AGENT_API_KEY = os.getenv("AGENT_API_KEY")
AGENT_API_URL = os.getenv("AGENT_API_URL")


def call_cortex(question: str):
    """Synchronous Cortex call. UNCHANGED behaviour, plus a timeout + status check
    so a failure surfaces cleanly instead of hanging forever."""
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
    response = requests.post(
        AGENT_API_URL,
        headers={
            "Authorization": f"Bearer {AGENT_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json=payload,
        timeout=600,  # don't hang forever; long agent runs allowed
    )
    response.raise_for_status()
    data = response.json()
    return parse_response(data)


def _run_job(job_id: str, question: str):
    """Runs the (blocking) Cortex call in a background THREAD so the event loop
    stays free to answer /status polls. Writes result/error into the job store."""
    try:
        result = call_cortex(question)
        job_store.set_done(job_id, result)
    except Exception as e:
        job_store.set_error(job_id, str(e))


def start_async_job(question: str) -> str:
    """Creates a job, kicks off the work in a daemon thread, returns job_id immediately."""
    job_id = job_store.create_job()
    t = threading.Thread(target=_run_job, args=(job_id, question), daemon=True)
    t.start()
    return job_id
