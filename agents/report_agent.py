import json
import logging
import os

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

SYSTEM_PROMPT = read_file(r"agents\system_prompt\report_system_prompt.txt")

def run_report_agent(message: str) -> dict:
    """
    Provides a detailed of complaint and process for the past 1 month. Returns a dict with these keys:
        summary: json string containing the summary of the complaint and process for the past 1 month.
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
        log.error(f"Report agent returned invalid JSON: {e}\nRaw: {raw}")
        return {
            "summary": "Sorry, I encountered an error while generating the report."
        }
