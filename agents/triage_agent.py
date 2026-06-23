import json
import logging
import os
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv

from utils.file_reader import read_file

load_dotenv()

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
)

SYSTEM_PROMPT = read_file(r"agents\system_prompt\triage_system_prompt.txt")

def run_triage_agent(message: str) -> dict:
    """
    Classifies the user's message and extracts key information.

    Returns a dict with these keys:
        intent            : CERTIFICATE | STATUS | COMPLAINT | UNKNOWN
        business_name     : str | None
        registration_number: str | None
        owner_name        : str | None
        follow_up         : str | None  — message to send user if info is missing
        ready             : bool        — True if pipeline can proceed
        summary           : str         — one sentence description of the request
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": message},
    ]

    response = client.chat.completions.create(
        model="qwen-plus",
        messages=messages,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown fences if model wraps in ```json
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        log.error(f"Triage agent returned invalid JSON: {e}\nRaw: {raw}")
        return {
            "intent": "UNKNOWN",
            "business_name": None,
            "registration_number": None,
            "owner_name": None,
            "follow_up": "Sorry, I didn't quite understand that. Could you tell me your full name and what you need help with?",
            "ready": False,
            "summary": "Could not parse user message"
        }

    log.info(f"Triage result — intent: {result.get('intent')} | ready: {result.get('ready')} | owner: {result.get('owner_name')}")
    return result


