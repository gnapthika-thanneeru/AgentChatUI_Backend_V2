import os
import requests
from app.utils.response_parser import parse_response
from dotenv import load_dotenv

load_dotenv()

AGENT_API_KEY = os.getenv("AGENT_API_KEY")
AGENT_API_URL = os.getenv("AGENT_API_URL")

if not AGENT_API_KEY:
    raise ValueError("AGENT_API_KEY not configured")

if not AGENT_API_URL:
    raise ValueError("AGENT_API_URL not configured")


def call_cortex(question: str):

    payload = {
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": question
                    }
                ]
            }
        ]
    }

    response = requests.post(
        AGENT_API_URL,
        headers={
            "Authorization": f"Bearer {AGENT_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        json=payload
    )

    data = response.json()

    return parse_response(data)
