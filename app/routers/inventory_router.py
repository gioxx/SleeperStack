from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.crypto import decrypt
from app.db import get_session
from app.models import Endpoint, User
from portainer_client import PortainerAPIError, get_all_containers

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _format_ports(ports):
    formatted = []
    for port in ports or []:
        public = port.get("PublicPort")
        private = port.get("PrivatePort")
        if public:
            formatted.append(f"{public}->{private}/{port.get('Type', 'tcp')}")
        else:
            formatted.append(f"{private}/{port.get('Type', 'tcp')}")
    return ", ".join(formatted)


def _first_ip(networks):
    for network in (networks or {}).values():
        if network.get("IPAddress"):
            return network["IPAddress"]
    return None


def _container_row(container):
    labels = container.get("Labels", {})
    networks = (container.get("NetworkSettings") or {}).get("Networks", {})
    created = container.get("Created")
    created_str = (
        datetime.fromtimestamp(created, tz=timezone.utc).isoformat() if created else None
    )
    return {
        "name": (container.get("Names", [None]) or [None])[0],
        "stack": labels.get("com.docker.compose.project"),
        "image": container.get("Image"),
        "state": container.get("State"),
        "status": container.get("Status"),
        "ports": _format_ports(container.get("Ports")),
        "ip": _first_ip(networks),
        "created": created_str,
        "autoshutdown": labels.get("autoshutdown"),
    }


@router.get("/inventory", response_class=HTMLResponse)
def inventory(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_session)):
    endpoint_views = []
    for endpoint in db.query(Endpoint).order_by(Endpoint.name).all():
        try:
            containers = get_all_containers(
                endpoint.portainer_url, decrypt(endpoint.api_key_encrypted), endpoint.endpoint_id
            )
            rows = [_container_row(c) for c in containers]
            error = None
        except PortainerAPIError as e:
            rows = None
            error = str(e)
        endpoint_views.append({"endpoint": endpoint, "containers": rows, "error": error})

    return templates.TemplateResponse(
        request, "inventory.html", {"user": user, "endpoint_views": endpoint_views}
    )
