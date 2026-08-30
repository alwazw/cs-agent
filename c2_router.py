import os
import asyncio
import random
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from typing import List
from calendar_service import schedule_appointment_override
from telemetry_service import telemetry_engine

router = APIRouter(prefix="/api/c2", tags=["C2 Dashboard Engine"])
DOCS_DIR = os.path.abspath("./docs")

class FileContentPayload(BaseModel):
    filepath: str
    content: str

class CalendarOverridePayload(BaseModel):
    customer_phone: str
    customer_name: str
    appointment_time: str
    service_name: str

# --- FILE MANAGEMENT C2 ENDPOINTS ---

@router.get("/files", response_model=List[str])
def list_knowledge_files():
    file_list = []
    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR, exist_ok=True)

    for root, _, files in os.walk(DOCS_DIR):
        for file in files:
            if file.endswith((".md", ".txt", ".json")):
                rel_path = os.path.relpath(os.path.join(root, file), DOCS_DIR)
                file_list.append(rel_path)
    return file_list

@router.get("/files/read")
def read_knowledge_file(filepath: str = Query(..., description="Relative path within /docs")):
    full_path = os.path.abspath(os.path.join(DOCS_DIR, filepath))
    if not full_path.startswith(DOCS_DIR) or not os.path.exists(full_path):
        raise HTTPException(status_code=400, detail="Access denied or file non-existent.")

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()
    return {"filepath": filepath, "content": content}

@router.post("/files/write")
def write_knowledge_file(payload: FileContentPayload):
    full_path = os.path.abspath(os.path.join(DOCS_DIR, payload.filepath))
    if not full_path.startswith(DOCS_DIR):
        raise HTTPException(status_code=400, detail="Access denied: Path traversal detected.")

    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(payload.content)
    return {"status": "success", "filepath": payload.filepath}

# --- CALENDAR OVERRIDE ENDPOINT ---

@router.post("/calendar/override")
async def trigger_calendar_override(payload: CalendarOverridePayload):
    result = await schedule_appointment_override(
        customer_phone=payload.customer_phone,
        customer_name=payload.customer_name,
        appointment_time=payload.appointment_time,
        service_name=payload.service_name
    )
    return result

# --- NOTIFICATION CENTER & ALERTS ---

@router.get("/alerts")
def get_alerts():
    """Fetch recent system alerts and token anomalies."""
    return {"alerts": telemetry_engine.get_alerts()}

# --- SIMULATED DEMO ENVIRONMENT ---

async def run_simulation_task(scenario: str):
    if scenario == "token_spike":
        # Simulate rapid token consumption burst
        for i in range(10):
            await telemetry_engine.register_token_usage(
                prompt_tokens=400,
                completion_tokens=300,
                session_id=f"sim_session_{i}"
            )
            await asyncio.sleep(0.05)
    elif scenario == "stack_failure":
        # Simulate component outage alert
        await telemetry_engine.log_health_issue(
            service_name="Docker Model Runner",
            message="GPU VRAM usage spiked to 99%. Model response latency > 8000ms.",
            severity="CRITICAL"
        )
    elif scenario == "normal":
        # Simulate standard traffic
        await telemetry_engine.register_token_usage(
            prompt_tokens=50,
            completion_tokens=30,
            session_id="sim_normal"
        )

@router.post("/demo/simulate")
async def simulate_traffic(scenario: str = Query("token_spike", enum=["token_spike", "stack_failure", "normal"]), background_tasks: BackgroundTasks = None):
    """Triggers a simulated environment test to validate notifications and stack metrics."""
    if background_tasks is not None:
        background_tasks.add_task(run_simulation_task, scenario)
    else:
        await run_simulation_task(scenario)
    return {"status": "simulation_started", "scenario": scenario}
