from apscheduler.triggers.cron import CronTrigger
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_session
from app.dependencies import get_scheduler
from app.models import Endpoint, Rule, User
from app.scheduler import SchedulerService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/rules", response_class=HTMLResponse)
def list_rules(
    request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_session)
):
    rules = db.query(Rule).order_by(Rule.id).all()
    endpoints = db.query(Endpoint).order_by(Endpoint.name).all()
    return templates.TemplateResponse(
        request, "rules.html", {"user": user, "rules": rules, "endpoints": endpoints, "error": None}
    )


@router.post("/rules")
def create_rule(
    request: Request,
    endpoint_id: int = Form(...),
    target_label: str = Form(...),
    action: str = Form(...),
    cron_expression: str = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
    scheduler: SchedulerService = Depends(get_scheduler),
):
    try:
        CronTrigger.from_crontab(cron_expression)
    except ValueError:
        rules = db.query(Rule).order_by(Rule.id).all()
        endpoints = db.query(Endpoint).order_by(Endpoint.name).all()
        return templates.TemplateResponse(
            request,
            "rules.html",
            {
                "user": user,
                "rules": rules,
                "endpoints": endpoints,
                "error": f"Invalid cron expression: {cron_expression}",
            },
            status_code=400,
        )

    rule = Rule(
        endpoint_id=endpoint_id,
        target_label=target_label,
        action=action,
        cron_expression=cron_expression,
        enabled=True,
    )
    db.add(rule)
    db.commit()
    scheduler.add_job(rule)
    return RedirectResponse(url="/rules", status_code=303)


@router.post("/rules/{rule_id}/toggle")
def toggle_rule(
    rule_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
    scheduler: SchedulerService = Depends(get_scheduler),
):
    rule = db.get(Rule, rule_id)
    if rule is not None:
        rule.enabled = not rule.enabled
        db.commit()
        if rule.enabled:
            scheduler.add_job(rule)
        else:
            scheduler.remove_job(rule.id)
    return RedirectResponse(url="/rules", status_code=303)


@router.post("/rules/{rule_id}/delete")
def delete_rule(
    rule_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
    scheduler: SchedulerService = Depends(get_scheduler),
):
    rule = db.get(Rule, rule_id)
    if rule is not None:
        scheduler.remove_job(rule.id)
        db.delete(rule)
        db.commit()
    return RedirectResponse(url="/rules", status_code=303)
