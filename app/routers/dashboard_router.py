import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.crypto import decrypt
from app.db import get_session
from app.models import Endpoint, RunHistory, User
from portainer_client import PortainerAPIError, get_all_containers, start_containers, stop_containers

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

AUTOSHUTDOWN_LABEL_KEY = "autoshutdown"


def _labeled_containers(endpoint):
    try:
        containers = get_all_containers(
            endpoint.portainer_url, decrypt(endpoint.api_key_encrypted), endpoint.endpoint_id
        )
    except PortainerAPIError as e:
        return None, str(e)

    rows = []
    for container in containers:
        labels = container.get("Labels", {})
        if AUTOSHUTDOWN_LABEL_KEY in labels:
            rows.append(
                {
                    "id": container.get("Id"),
                    "name": (container.get("Names", [None]) or [None])[0],
                    "state": container.get("State"),
                    "label_value": labels[AUTOSHUTDOWN_LABEL_KEY],
                }
            )
    return rows, None


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_session)):
    endpoint_views = []
    for endpoint in db.query(Endpoint).order_by(Endpoint.name).all():
        rows, error = _labeled_containers(endpoint)
        endpoint_views.append({"endpoint": endpoint, "containers": rows, "error": error})

    return templates.TemplateResponse(
        request, "dashboard.html", {"user": user, "endpoint_views": endpoint_views}
    )


@router.post("/dashboard/{endpoint_id}/containers/{container_id}/{action}")
def manual_action(
    endpoint_id: int,
    container_id: str,
    action: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    endpoint = db.get(Endpoint, endpoint_id)
    if endpoint is not None and action in ("stop", "start"):
        api_key = decrypt(endpoint.api_key_encrypted)
        target = [(container_id, None, "running" if action == "stop" else "exited")]
        history = RunHistory(rule_id=None, status="running", dry_run=False)
        db.add(history)
        db.commit()

        try:
            if action == "stop":
                results = stop_containers(endpoint.portainer_url, api_key, endpoint.endpoint_id, target)
            else:
                results = start_containers(endpoint.portainer_url, api_key, endpoint.endpoint_id, target)
            history.status = "success"
            history.detail_json = json.dumps({"results": results})
        except PortainerAPIError as e:
            history.status = "error"
            history.detail_json = json.dumps({"error": str(e)})
        db.commit()

    return RedirectResponse(url="/dashboard", status_code=303)
