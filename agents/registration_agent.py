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

SYSTEM_PROMPT = read_file(r"agents/system_prompt/registration_system_prompt.txt")

REGISTRATION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "await_email",
            "description": (
                "Use when the business is registered and you need the user's email "
                "to send their certificate. Stores context for the next pipeline step."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Warm message to send to the user asking for their email address"
                    },
                    "owner_name": {
                        "type": "string",
                        "description": "Full name of the business owner"
                    },
                    "business_name": {
                        "type": "string",
                        "description": "Registered business name"
                    },
                    "registration_number": {
                        "type": "string",
                        "description": "CAC registration number"
                    },
                    "certificate_url": {
                        "type": "string",
                        "description": "Path or URL to the certificate PDF. Null if not available."
                    },
                    "extra_info": {
                        "type": "string",
                        "description": "Any additional context to include in the certificate email body"
                    }
                },
                "required": ["message", "owner_name", "business_name", "registration_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "await_docs",
            "description": (
                "Use when the business registration is pending due to missing documents. "
                "Tells the user what is missing and waits for them to resubmit."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Message to send to the user listing the missing documents"
                    },
                    "missing_docs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of missing document names"
                    }
                },
                "required": ["message", "missing_docs"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "resolve_complaint",
            "description": (
                "Use when the complaint is fully resolved — registration is processing "
                "on schedule and the user has been given a timeline. Closes the complaint."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Final message to send to the user confirming their status"
                    },
                    "resolution_method": {
                        "type": "string",
                        "description": "Brief description of how it was resolved e.g. 'processing_timeline_given'"
                    }
                },
                "required": ["message", "resolution_method"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_complaint",
            "description": (
                "Use when the complaint cannot be resolved automatically — business not found, "
                "rejected, unknown pending reason, or any situation requiring human intervention."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Warm message to send to the user explaining that a staff member will follow up"
                    },
                    "escalation_reason": {
                        "type": "string",
                        "description": "Internal reason for escalation — factual, for staff context"
                    }
                },
                "required": ["message", "escalation_reason"]
            }
        }
    }
]

def execute_registration_tool(tool_name: str, tool_args: dict, context: dict) -> tuple[str, dict]:
    """
    Executes the registration tool called by the agent.

    Returns:
        (tool_result_str, state_update) where state_update is a dict
        the pipeline uses to decide the next step.
    """
    complaint_id = context.get("complaint_id")

    if tool_name == "await_email":
        log.info(f"Complaint {complaint_id}: awaiting email from user")
        state = {
            "action": "AWAIT_EMAIL",
            "message": tool_args["message"],
            "email_context": {
                "owner_name": tool_args["owner_name"],
                "business_name": tool_args["business_name"],
                "registration_number": tool_args["registration_number"],
                "certificate_url": tool_args.get("certificate_url"),
                "extra_info": tool_args.get("extra_info", ""),
            }
        }
        return json.dumps({"status": "awaiting_email"}), state

    if tool_name == "await_docs":
        log.info(f"Complaint {complaint_id}: awaiting documents — {tool_args['missing_docs']}")
        state = {
            "action": "AWAIT_DOCS",
            "message": tool_args["message"],
            "missing_docs": tool_args["missing_docs"]
        }
        return json.dumps({"status": "awaiting_docs"}), state

    if tool_name == "resolve_complaint":
        log.info(f"Complaint {complaint_id}: resolved — {tool_args['resolution_method']}")
        state = {
            "action": "RESOLVED",
            "message": tool_args["message"],
            "resolution_method": tool_args["resolution_method"]
        }
        return json.dumps({"status": "resolved"}), state

    if tool_name == "escalate_complaint":
        log.info(f"Complaint {complaint_id}: escalating — {tool_args['escalation_reason']}")
        state = {
            "action": "ESCALATE",
            "message": tool_args["message"],
            "escalation_reason": tool_args["escalation_reason"]
        }
        return json.dumps({"status": "escalated"}), state

    return json.dumps({"error": f"Unknown tool: {tool_name}"}), {}

def run_registration_agent(context: dict) -> dict:
    """
    Runs the Registration Agent with the given context.

    context keys:
        user_message     : str        — the user's original WhatsApp message
        owner_name       : str        — full name of the business owner
        complaint_id     : int        — ID of the complaint record in Supabase
        business_record  : dict|None  — the business record from Supabase

    Returns a state dict with keys:
        action           : AWAIT_EMAIL | AWAIT_DOCS | RESOLVED | ESCALATE
        message          : str — what to send the user on WhatsApp
        + action-specific fields
    """
    user_content = f"""
User message: {context.get("user_message")}
Owner name: {context.get("owner_name")}
Complaint ID: {context.get("complaint_id")}
Business record: {json.dumps(context.get("business_record"), indent=2)}
"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_content},
    ]

    final_state = {}

    while True:
        response = client.chat.completions.create(
            model="qwen-plus",
            messages=messages,
            tools=REGISTRATION_TOOLS,
            tool_choice="auto",
        )

        choice = response.choices[0]

        if choice.finish_reason == "tool_calls":
            tool_calls = choice.message.tool_calls
            messages.append(choice.message)

            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                log.info(f"Registration agent calling: {tool_name}")
                result_str, state = execute_registration_tool(tool_name, tool_args, context)

                if state:
                    final_state = state

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_str,
                })
            continue

        # Agent finished — return accumulated state
        if not final_state:
            log.warning("Registration agent finished without calling a tool — escalating as fallback")
            final_state = {
                "action": "ESCALATE",
                "message": "We encountered an issue processing your request. A staff member will follow up shortly.",
                "escalation_reason": "Agent finished without calling any tool"
            }

        return final_state
