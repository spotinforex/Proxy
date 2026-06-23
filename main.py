import asyncio
import logging
import os
import re
import time

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.websockets import WebSocket, WebSocketDisconnect


from logic.websocket import ConnectionManager
from utils.is_duplicate import is_duplicate, DEDUP_TTL, _seen_ids
from pipeline.process import debounce_pipeline, _debounce_timers, _message_buffers
from pipeline.run_agent_process import run_pipeline, run_pipeline_with_filter, fetch_data_feed
from logic.processor import complaint_processor
from pydantic import BaseModel
from typing import Optional

load_dotenv()

WEBHOOK_TOKEN = os.getenv("WEBHOOK_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("proxy")

app = FastAPI(title="Proxy", description="Autonomous program operations agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

bearer_scheme = HTTPBearer(auto_error=False)

manager = ConnectionManager()


class PipelineFilterRequest(BaseModel):
    complaint_type: Optional[str] = None
    status: Optional[str] = None


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)


async def verify_token(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)):
    if not credentials or credentials.credentials != WEBHOOK_TOKEN:
        logger.warning("Unauthorized webhook request — invalid or missing token.")
        raise HTTPException(status_code=401, detail="Unauthorized")
    return credentials


@app.post("/webhook")
async def webhook(request: Request, credentials: HTTPAuthorizationCredentials = Security(verify_token)):
    try:
        data = await request.json()
        logger.info(f"Incoming webhook: {data}")
        type_webhook = data.get("typeWebhook")

        # Deduplicate
        id_message = data.get("idMessage")
        if id_message and is_duplicate(id_message):
            logger.info(f"Duplicate webhook ignored: {id_message}")
            return JSONResponse({"status": "duplicate"}, status_code=200)

        # Only process incoming messages
        if type_webhook != "incomingMessageReceived":
            return JSONResponse({"status": "ignored"}, status_code=200)

        result = complaint_processor(data)
        if not result:
            logger.warning("complaint_processor returned None — skipping pipeline")
            return JSONResponse({"status": "ignored"}, status_code=200)

        sender, message, timestamp = result

        # Broadcast to dashboard via WebSocket
        await manager.broadcast({
            "event": "new_message",
            "sender": sender,
            "message": message,
            "timestamp": timestamp,
        })

        _message_buffers.setdefault(sender, []).append(message)

        # Cancel existing debounce for this sender if mid-burst
        existing = _debounce_timers.get(sender)
        if existing and not existing.done():
            existing.cancel()

        task = asyncio.create_task(debounce_pipeline(sender))
        _debounce_timers[sender] = task
        task.add_done_callback(
        lambda t: logger.error(f"Pipeline failed for {sender}: {t.exception()}")
        if not t.cancelled() and t.exception()
        else None
        )
        return JSONResponse({"status": "ok"}, status_code=200)

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)

@app.get("/health")
async def health():
    return {"status": "Proxy is running"}


@app.get("/api/pipeline/data")
async def get_pipeline_data(credentials: HTTPAuthorizationCredentials = Security(verify_token)):
    """
    Fetch all complaints and actions from past month without running through agent.
    """
    try:
        logger.info("Fetching pipeline data feed...")
        data = fetch_data_feed()
        return {
            "status": "success",
            "complaints_count": len(data.get("complaints", [])),
            "actions_count": len(data.get("actions", [])),
            "data": data
        }
    except Exception as e:
        logger.error(f"Error fetching pipeline data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pipeline/report")
async def generate_management_report(credentials: HTTPAuthorizationCredentials = Security(verify_token)):
    """
    Run full management report pipeline:
    - Fetches all complaints and actions from past month
    - Processes through report agent
    - Returns agent analysis and data summary
    """
    try:
        logger.info("Running management report pipeline...")
        result = run_pipeline()
        logger.info(f"Management report completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Error running management report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pipeline/report/filtered")
async def generate_filtered_report(
    request: PipelineFilterRequest,
    credentials: HTTPAuthorizationCredentials = Security(verify_token)
):
    """
    Run filtered management report pipeline with optional filters:
    - complaint_type: Filter by specific complaint type
    - status: Filter by complaint status
    """
    try:
        logger.info(f"Running filtered pipeline (type={request.complaint_type}, status={request.status})...")
        result = run_pipeline_with_filter(
            complaint_type=request.complaint_type,
            status=request.status
        )
        logger.info(f"Filtered report completed: {result.get('status')}")
        return result
    except Exception as e:
        logger.error(f"Error running filtered report: {e}")
        raise HTTPException(status_code=500, detail=str(e))