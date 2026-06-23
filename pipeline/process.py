import asyncio
import logging, os

from logic.db import Database
from logic.message_handler import send_message

from agents.triage_agent import run_triage_agent
from agents.registration_agent import run_registration_agent
from logic.message_handler import send_message
from logic.email_handler import execute_email_tool
from utils.session_memory import log_memory, get_memory

STAFF_EMAIL = os.getenv("STAFF_EMAIL")

logger = logging.getLogger("pipeline")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pipeline")

_debounce_timers: dict[str, asyncio.Task] = {}
_message_buffers: dict[str, list[str]] = {}
DEBOUNCE_SECONDS = 3

db = Database()

_conversation_state: dict[str, dict] = {}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_triage_context(phone: str, triage: dict) -> dict:
    """Merge accumulated triage data across multiple messages."""
    existing = _conversation_state.get(phone, {})
    return {
        "intent":               triage.get("intent")               or existing.get("intent"),
        "owner_name":           triage.get("owner_name")           or existing.get("owner_name"),
        "business_name":        triage.get("business_name")        or existing.get("business_name"),
        "registration_number":  triage.get("registration_number")  or existing.get("registration_number"),
        "summary":              triage.get("summary")              or existing.get("summary"),
    }

# ── Pipeline ──────────────────────────────────────────────────────────────────

async def run_pipeline(phone: str, message: str):  
    """
    Main resolution pipeline.

    1. Check if phone is mid-conversation (awaiting email or docs)
    2. Triage — classify intent, extract info
    3. If info missing — ask follow-up, store partial state, return
    4. Create complaint record in DB
    5. Look up business in DB
    6. Run Registration Agent — get action decision
    7. Act on decision — send message, update DB, log action
    """
    try:
        logger.info(f"Running pipeline for {phone}: {message}")

        # ── Step 1: Handle mid-conversation state ─────────────────────────────

        state = _conversation_state.get(phone, {})

        if state.get("action") == "AWAIT_EMAIL":
            await _handle_email_reply(phone, message, state)
            return

        if state.get("action") == "AWAIT_DOCS":
            await _handle_docs_reply(phone, message, state)
            return
        
        if get_memory(phone):
            message += f"\n\nConversation history:\n{get_memory(phone)}"

        # ── Step 2: Triage ────────────────────────────────────────────────────
        triage = run_triage_agent(message)
        log_memory(phone, message, triage.get("follow_up", "No summary available"))
        ctx = _build_triage_context(phone, triage)

        if not triage.get("ready"):
            # Store partial context so next message can complete it
            _conversation_state[phone] = {**state, **ctx}
            await send_message(to=phone, text=triage["follow_up"])
            db.log_action(
                complaint_id=state.get("complaint_id"),
                action_type="triage_follow_up",
                outcome=triage["follow_up"]
            ) if state.get("complaint_id") else None
            logger.info(f"Triage incomplete for {phone} — follow-up sent")
            return

        # ── Step 3: Create complaint record ───────────────────────────────────

        complaint_id = db.create_complaint(
            whatsapp_number=int(phone),
            message=message,
            business_name=ctx.get("business_name"),
            complaint_type=ctx.get("intent"),
        )

        if not complaint_id:
            logger.error(f"Failed to create complaint record for {phone}")
            await send_message(
                to=phone,
                text="Sorry, we encountered an issue logging your request. Please try again shortly."
            )
            return

        logger.info(f"Complaint {complaint_id} created for {phone}")

        db.log_action(
            complaint_id=complaint_id,
            action_type="triage_complete",
            outcome=triage.get("summary")
        )

        # ── Step 4: Look up business ──────────────────────────────────────────

        business = db.get_business(
            business_name=ctx.get("business_name"),
            registration_number=ctx.get("registration_number"),
            owner_name=ctx.get("owner_name"),
        )

        logger.info(f"Business lookup for complaint {complaint_id}: {'found' if business else 'not found'}")

        # ── Step 5: Registration Agent ────────────────────────────────────────

        agent_result = run_registration_agent({
            "user_message":      message,
            "owner_name":        ctx.get("owner_name"),
            "complaint_id":      complaint_id,
            "business_record":   dict(business) if business else None,
        })

        action  = agent_result.get("action")
        msg_out = agent_result.get("message")

        logger.info(f"Registration agent action: {action} for complaint {complaint_id}")

        # ── Step 6: Act on decision ───────────────────────────────────────────

        await send_message(to=phone, text=msg_out)

        if action == "AWAIT_EMAIL":
            _conversation_state[phone] = {
                "action":       "AWAIT_EMAIL",
                "complaint_id": complaint_id,
                "email_context": agent_result.get("email_context", {}),
            }
            db.log_action(
                complaint_id=complaint_id,
                action_type="await_email",
                outcome="Waiting for user to provide email address"
            )

        elif action == "AWAIT_DOCS":
            _conversation_state[phone] = {
                "action":       "AWAIT_DOCS",
                "complaint_id": complaint_id,
                "missing_docs": agent_result.get("missing_docs", []),
            }
            db.log_action(
                complaint_id=complaint_id,
                action_type="await_docs",
                outcome=f"Missing docs: {', '.join(agent_result.get('missing_docs', []))}"
            )

        elif action == "RESOLVED":
            db.resolve_complaint(
                complaint_id=complaint_id,
                resolution_method=agent_result.get("resolution_method", "agent_resolved"),
                notes=msg_out
            )
            db.log_action(
                complaint_id=complaint_id,
                action_type="resolved",
                outcome=agent_result.get("resolution_method")
            )
            _conversation_state.pop(phone, None)

        elif action == "ESCALATE":
            db.escalate_complaint(
                complaint_id=complaint_id,
                assigned_to="Brown",
                notes=agent_result.get("escalation_reason")
            )
            body = f"""
            Complaint ID: {complaint_id}

            Phone Number: {phone}
            Business Name: {ctx.get('business_name')}
            Owner Name: {ctx.get('owner_name')}

            Customer Message:
            {message}

            Escalation Reason:
            {agent_result.get('escalation_reason')}

            Please review and follow up with the customer.
            """
            asyncio.create_task(
            asyncio.to_thread(
                execute_email_tool,
                "notify_staff",
                {
                    "staff_email": STAFF_EMAIL,
                    "subject": f"Complaint #{complaint_id} requires attention",
                    "body": body
                    }
                )
            )
            db.log_action(
                complaint_id=complaint_id,
                action_type="escalated",
                outcome=agent_result.get("escalation_reason")
            )
            _conversation_state.pop(phone, None)

        logger.info(f"Pipeline complete for {phone} — complaint {complaint_id} → {action}")

    except Exception as e:
        logger.error(f"Pipeline error for {phone}: {e}")
        await send_message(
            to=phone,
            text="We encountered an unexpected error. Please try again or contact us directly."
        )

async def _handle_email_reply(phone: str, email: str, state: dict):
    """User has replied with their email address — send certificate."""
    complaint_id  = state.get("complaint_id")
    email_context = state.get("email_context", {})
    email         = email.strip()

    logger.info(f"Email reply from {phone} for complaint {complaint_id}: {email}")

    result = execute_email_tool("send_certificate_email", {
        "recipient_email":    email,
        "subject":            f"Your CAC Registration Certificate — {email_context.get('business_name')}",
        "body":               email_context.get("extra_info", "Please find your certificate attached."),
        "owner_name":         email_context.get("owner_name"),
        "business_name":      email_context.get("business_name"),
        "registration_number": email_context.get("registration_number"),
        "certificate_path":   email_context.get("certificate_url"),
    })

    await send_message(
        to=phone,
        text=f"Your certificate has been sent to {email}. Please check your inbox. Congratulations once again! 🎉"
    )

    db.resolve_complaint(
        complaint_id=complaint_id,
        resolution_method="certificate_emailed",
        notes=f"Certificate sent to {email}"
    )
    db.log_action(
        complaint_id=complaint_id,
        action_type="certificate_emailed",
        outcome=f"Sent to {email}"
    )

    _conversation_state.pop(phone, None)
    logger.info(f"Certificate emailed for complaint {complaint_id} — complaint resolved")


async def _handle_docs_reply(phone: str, message: str, state: dict):
    """User has replied after being asked for missing documents."""
    complaint_id = state.get("complaint_id")

    logger.info(f"Docs reply from {phone} for complaint {complaint_id}: {message}")

    # Acknowledge receipt and escalate to staff to verify
    await send_message(
        to=phone,
        text="Thank you for sending that. Our team will review your documents and update you shortly."
    )

    db.escalate_complaint(
        complaint_id=complaint_id,
        assigned_to="staff",
        notes=f"User submitted documents: {message}"
    )
    db.log_action(
        complaint_id=complaint_id,
        action_type="docs_received",
        outcome=f"User reply: {message}"
    )

    _conversation_state.pop(phone, None)
    logger.info(f"Docs received for complaint {complaint_id} — escalated to staff")


async def debounce_pipeline(phone: str):
    """Debounce rapid messages from the same phone number."""
    await asyncio.sleep(DEBOUNCE_SECONDS)
    
    # Only pop after sleep — buffer has had time to accumulate
    messages = _message_buffers.pop(phone, [])
    if not messages:
        return
    
    merged_message = " ".join(messages)
    logger.info(f"Merged {len(messages)} messages for {phone}: {merged_message}")
    
    await run_pipeline(phone, merged_message)
