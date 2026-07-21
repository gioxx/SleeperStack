from apscheduler.triggers.cron import CronTrigger
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.cron_import import parse_crontab_text
from app.db import get_session
from app.dependencies import get_scheduler
from app.models import Endpoint, Rule, User
from app.scheduler import SchedulerService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _match_endpoint(db, portainer_url, endpoint_id_value):
    return (
        db.query(Endpoint)
        .filter_by(portainer_url=portainer_url, endpoint_id=endpoint_id_value)
        .one_or_none()
    )


@router.get("/rules/import", response_class=HTMLResponse)
def import_form(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse(request, "import_cron.html", {"user": user, "preview": None})


@router.post("/rules/import/preview", response_class=HTMLResponse)
def import_preview(
    request: Request,
    crontab_text: str = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    parsed_lines = parse_crontab_text(crontab_text)
    preview = []
    for parsed in parsed_lines:
        if not parsed.is_valid:
            preview.append({"parsed": parsed, "endpoint": None})
            continue
        endpoint = _match_endpoint(db, parsed.portainer_url, parsed.endpoint_id)
        if endpoint is None:
            parsed.error = f"No configured endpoint matches {parsed.portainer_url} (id {parsed.endpoint_id})"
        preview.append({"parsed": parsed, "endpoint": endpoint})

    return templates.TemplateResponse(
        request,
        "import_cron.html",
        {"user": user, "preview": preview, "crontab_text": crontab_text},
    )


@router.post("/rules/import/confirm")
def import_confirm(
    request: Request,
    cron_expression: list[str] = Form(...),
    action: list[str] = Form(...),
    target_label: list[str] = Form(...),
    endpoint_db_id: list[str] = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
    scheduler: SchedulerService = Depends(get_scheduler),
):
    for cron, act, label, endpoint_id in zip(cron_expression, action, target_label, endpoint_db_id):
        try:
            CronTrigger.from_crontab(cron)
        except ValueError:
            continue
        rule = Rule(
            endpoint_id=int(endpoint_id),
            target_label=label,
            action=act,
            cron_expression=cron,
            enabled=True,
        )
        db.add(rule)
        db.commit()
        scheduler.add_job(rule)

    return RedirectResponse(url="/rules", status_code=303)
