import json
import logging
from typing import List, Dict, Any

from logic.db import Database
from agents.report_agent import run_report_agent

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def fetch_data_feed() -> Dict[str, Any]:
    """
    Fetch all complaints and actions from past month for management reporting.
    Returns a dict with complaints and actions lists.
    """
    db = None
    try:
        db = Database()
        complaints = db.get_all_complaints_past_month()
        actions = db.get_all_actions_past_month()

        log.info(f"Fetched {len(complaints) if complaints else 0} complaints and {len(actions) if actions else 0} actions from past month")
        return {
            "complaints": complaints or [],
            "actions": actions or []
        }
    except Exception as e:
        log.error(f"Error fetching data feed: {e}")
        return {"complaints": [], "actions": []}
    finally:
        if db:
            db.close()


def format_data_for_agent(data: Dict[str, Any]) -> str:
    """
    Format complaint and action data into a structured message for management report.
    """
    complaints = data.get("complaints", [])
    actions = data.get("actions", [])

    if not complaints and not actions:
        return "No complaints or actions to process for the past month."

    formatted_message = "MANAGEMENT REPORT - PAST MONTH DATA\n"
    formatted_message += "=" * 50 + "\n\n"

    # Complaints Section
    formatted_message += f"COMPLAINTS SUMMARY (Total: {len(complaints)})\n"
    formatted_message += "-" * 50 + "\n"
    if complaints:
        for complaint in complaints:
            formatted_message += f"""
ID: {complaint.get('id')}
Business: {complaint.get('business_name')}
Type: {complaint.get('complaint_type')}
Status: {complaint.get('status')}
Message: {complaint.get('message')}
WhatsApp: {complaint.get('whatsapp_number')}
Created: {complaint.get('first_response_at')}
Resolved: {complaint.get('resolved_at')}
Resolution Method: {complaint.get('resolution_method')}
Assigned To: {complaint.get('assigned_to')}
---
"""
    else:
        formatted_message += "No complaints in past month.\n"

    formatted_message += "\n"

    # Actions Section
    formatted_message += f"ACTIONS TAKEN (Total: {len(actions)})\n"
    formatted_message += "-" * 50 + "\n"
    if actions:
        for action in actions:
            formatted_message += f"""
Complaint ID: {action.get('complaint_id')}
Action Type: {action.get('action_type')}
Taken At: {action.get('taken_at')}
Outcome: {action.get('outcome')}
Staff Notified: {action.get('staff_notified')}
---
"""
    else:
        formatted_message += "No actions taken in past month.\n"

    return formatted_message


def run_pipeline() -> Dict[str, Any]:
    """
    Main pipeline for management reporting:
    1. Fetch all complaints and actions from past month
    2. Format data for agent processing
    3. Run report agent with the data
    4. Return the response
    """
    try:
        log.info("Starting management report pipeline...")

        # Step 1: Fetch data feed
        log.info("Step 1: Fetching complaints and actions from past month...")
        data = fetch_data_feed()
        complaints_count = len(data.get("complaints", []))
        actions_count = len(data.get("actions", []))

        if not complaints_count and not actions_count:
            log.warning("No data found in past month")
            return {
                "status": "no_data",
                "message": "No complaints or actions in past month",
                "result": None
            }

        # Step 2: Format data for agent
        log.info(f"Step 2: Formatting {complaints_count} complaints and {actions_count} actions...")
        formatted_message = format_data_for_agent(data)

        # Step 3: Run agent with formatted data
        log.info("Step 3: Running report agent for management analysis...")
        agent_response = run_report_agent(formatted_message)

        # Step 4: Return structured response
        log.info("Step 4: Pipeline completed successfully")
        return {
            "status": "success",
            "complaints_count": complaints_count,
            "actions_count": actions_count,
            "period": "past_month",
            "agent_response": agent_response,
            "data": {
                "complaints": data.get("complaints", []),
                "actions": data.get("actions", [])
            }
        }

    except Exception as e:
        log.error(f"Pipeline execution failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "result": None
        }


def run_pipeline_with_filter(complaint_type: str = None, status: str = None) -> Dict[str, Any]:
    """
    Advanced pipeline with filtering options for management report.
    """
    db = None
    try:
        log.info(f"Starting filtered management report (type={complaint_type}, status={status})...")
        db = Database()

        # Fetch all complaints and actions
        complaints = db.get_all_complaints_past_month() or []
        actions = db.get_all_actions_past_month() or []

        # Apply complaint filters
        if complaint_type:
            complaints = [c for c in complaints if c.get('complaint_type') == complaint_type]
        if status:
            complaints = [c for c in complaints if c.get('status') == status]

        log.info(f"Filtered to {len(complaints)} complaints and {len(actions)} actions")

        if not complaints and not actions:
            return {
                "status": "no_data",
                "message": "No data matching filter criteria",
                "result": None
            }

        # Format and process through agent
        data = {"complaints": complaints, "actions": actions}
        formatted_message = format_data_for_agent(data)
        agent_response = run_report_agent(formatted_message)

        return {
            "status": "success",
            "complaints_count": len(complaints),
            "actions_count": len(actions),
            "filters": {"type": complaint_type, "status": status},
            "period": "past_month",
            "agent_response": agent_response,
            "data": data
        }

    except Exception as e:
        log.error(f"Filtered pipeline failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "result": None
        }
    finally:
        if db:
            db.close()

