import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("processor")

def complaint_processor(data: dict) -> tuple[str, str, str] | None:
    """
    Extract sender, message text, and timestamp from Green API payload.
    Returns None if the message should be ignored.
    """
    try:
        sender_data = data.get("senderData", {})
        message_data = data.get("messageData", {})

        chat_id = sender_data.get("chatId", "")
        timestamp = data.get("timestamp", "")

        # Only handle direct messages not group chats
        if not chat_id.endswith("@c.us"):
            logger.info("Ignoring non-direct message")
            return None

        # Extract phone number
        match = re.search(r"(\d+)@", chat_id)
        phone = match.group(1) if match else None
        if not phone:
            logger.warning("Could not extract phone number")
            return None

        # Extract message text
        text_data = message_data.get("textMessageData", {})
        message = text_data.get("textMessage", "").strip()

        if not message:
            logger.info("Empty message — ignoring")
            return None

        return phone, message, str(timestamp)

    except Exception as e:
        logger.error(f"complaint_processor error: {e}")
        return None
