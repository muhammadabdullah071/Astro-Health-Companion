from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.db.database import get_db
from app.engine import service
from app.errors import AppError
from app.services import rag_adapter

router = APIRouter()


class AskBody(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    alert_id: Optional[str] = None


@router.post("/assistant/ask")
def ask(body: AskBody, conn=Depends(get_db)):
    alert = None
    if body.alert_id:
        alert = service.fetch_alert(conn, body.alert_id)
        if alert is None:
            raise AppError(404, "NOT_FOUND", "Alert not found.")
    return rag_adapter.answer_question(body.question, alert)
