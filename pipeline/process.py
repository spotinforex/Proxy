import asyncio
import logging

from logic.db import Database
from logic.message_handler import send_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pipeline")

_debounce_timers: dict[str, asyncio.Task] = {}
_message_buffers: dict[str, list[str]] = {}
DEBOUNCE_SECONDS = 3

db = Database()

async def run_pipeline(phone: str, message: str, data: dict):
    """
    Main resolution pipeline.
    1. Classify complaint via Qwen
    2. Look up business in Supabase
    3. Resolve, escalate, or request more info
    4. Log every action
    """
    try:
        logger.info(f"Running pipeline for {phone}: {message}")

        # TODO: Step 1 — Qwen classification
        # complaint_type, business_name = await classify_message(message)

        # TODO: Step 2 — Create complaint record
        # complaint_id = db.create_complaint(int(phone), message, business_name, complaint_type)

        # TODO: Step 3 — Look up business
        # business = db.get_business(business_name=business_name)

        # TODO: Step 4 — Resolution logic
        # await resolve(phone, complaint_id, business)
        status = await send_message(to=phone, text=message)
        logger.info(f"Pipeline complete for {phone}")

    except Exception as e:
        logger.error(f"Pipeline error for {phone}: {e}")


async def debounce_pipeline(phone: str, data: dict):
    await asyncio.sleep(DEBOUNCE_SECONDS)
    
    # Only pop after sleep — buffer has had time to accumulate
    messages = _message_buffers.pop(phone, [])
    if not messages:
        return
    
    merged_message = " ".join(messages)
    logger.info(f"Merged {len(messages)} messages for {phone}: {merged_message}")
    
    await run_pipeline(phone, merged_message, data)


