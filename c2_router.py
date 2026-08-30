import os
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List
from calendar_service import schedule_appointment_override

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
    """Lists all manageable document files inside the /docs folder."""
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
    """Reads raw text content of a target knowledge file."""
    full_path = os.path.abspath(os.path.join(DOCS_DIR, filepath))
    if not full_path.startswith(DOCS_DIR) or not os.path.exists(full_path):
        raise HTTPException(status_code=400, detail="Access denied or file non-existent.")

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()
    return {"filepath": filepath, "content": content}

@router.post("/files/write")
def write_knowledge_file(payload: FileContentPayload):
    """Writes or overwrites content to a target file in /docs without restarting server."""
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
    """Triggers an agent manual override to schedule calendar slots without payment."""
    result = await schedule_appointment_override(
        customer_phone=payload.customer_phone,
        customer_name=payload.customer_name,
        appointment_time=payload.appointment_time,
        service_name=payload.service_name
    )
    return result
