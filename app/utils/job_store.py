"""
In-memory job store for async question handling.
NOTE: This is safe ONLY when App Runner max instances = 1 (single instance),
because jobs live in this process's memory. If scaled to multiple instances,
a /status poll could hit an instance that never saw the job. For multi-instance,
replace this with a shared store (Snowflake table / Redis).
"""
import threading
import time
import uuid

_jobs = {}
_lock = threading.Lock()

# Auto-expire finished jobs after this many seconds to avoid unbounded memory growth.
_TTL_SECONDS = 1800  # 30 min


def create_job() -> str:
    job_id = str(uuid.uuid4())
    with _lock:
        _jobs[job_id] = {
            "status": "pending",   # pending | done | error
            "result": None,
            "error": None,
            "created_at": time.time(),
        }
    return job_id


def set_done(job_id: str, result):
    with _lock:
        if job_id in _jobs:
            _jobs[job_id]["status"] = "done"
            _jobs[job_id]["result"] = result


def set_error(job_id: str, message: str):
    with _lock:
        if job_id in _jobs:
            _jobs[job_id]["status"] = "error"
            _jobs[job_id]["error"] = message


def get_job(job_id: str):
    _cleanup()
    with _lock:
        job = _jobs.get(job_id)
        return dict(job) if job else None


def _cleanup():
    now = time.time()
    with _lock:
        stale = [k for k, v in _jobs.items() if now - v["created_at"] > _TTL_SECONDS]
        for k in stale:
            _jobs.pop(k, None)
