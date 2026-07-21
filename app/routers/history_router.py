from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_session
from app.models import RunHistory, User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/history", response_class=HTMLResponse)
def list_history(
    request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_session)
):
    entries = db.query(RunHistory).order_by(desc(RunHistory.started_at)).limit(200).all()
    return templates.TemplateResponse(request, "history.html", {"user": user, "entries": entries})
