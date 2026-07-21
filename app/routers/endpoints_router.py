from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.crypto import decrypt, encrypt
from app.db import get_session
from app.models import Endpoint, User
from portainer_client import PortainerAPIError, get_all_containers

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/endpoints", response_class=HTMLResponse)
def list_endpoints(
    request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_session)
):
    endpoints = db.query(Endpoint).order_by(Endpoint.name).all()
    return templates.TemplateResponse(
        request, "endpoints.html", {"user": user, "endpoints": endpoints, "error": None}
    )


@router.post("/endpoints")
def create_endpoint(
    name: str = Form(...),
    portainer_url: str = Form(...),
    api_key: str = Form(...),
    endpoint_id: str = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    db.add(
        Endpoint(
            name=name,
            portainer_url=portainer_url.rstrip("/"),
            api_key_encrypted=encrypt(api_key),
            endpoint_id=endpoint_id,
        )
    )
    db.commit()
    return RedirectResponse(url="/endpoints", status_code=303)


@router.post("/endpoints/{endpoint_id}/delete")
def delete_endpoint(
    endpoint_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    endpoint = db.get(Endpoint, endpoint_id)
    if endpoint is not None:
        db.delete(endpoint)
        db.commit()
    return RedirectResponse(url="/endpoints", status_code=303)


@router.post("/endpoints/{endpoint_id}/test", response_class=HTMLResponse)
def test_endpoint(
    request: Request,
    endpoint_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    endpoints = db.query(Endpoint).order_by(Endpoint.name).all()
    endpoint = db.get(Endpoint, endpoint_id)
    error = None
    if endpoint is None:
        error = "Endpoint not found"
    else:
        try:
            containers = get_all_containers(
                endpoint.portainer_url, decrypt(endpoint.api_key_encrypted), endpoint.endpoint_id
            )
            error = f"OK - {len(containers)} container(s) found"
        except PortainerAPIError as e:
            error = f"Connection failed: {e}"

    return templates.TemplateResponse(
        request, "endpoints.html", {"user": user, "endpoints": endpoints, "error": error}
    )
