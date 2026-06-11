# Cortex Backend

FastAPI backend for Power BI Custom Visual integrated with Snowflake Cortex Agent.

## Run Locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Environment Variables

Create a `.env` file:

```env
AGENT_API_KEY=xxxx
AGENT_API_URL=xxxx
```

Open Swagger:

http://localhost:8000/docs