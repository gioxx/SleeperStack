from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse

import app.db as db
from app.auth import NotAuthenticated, bootstrap_admin
from app.routers import auth_router, dashboard_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db(bind_engine=db.engine)
    session = db.SessionLocal()
    try:
        bootstrap_admin(session)
    finally:
        session.close()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(auth_router.router)
app.include_router(dashboard_router.router)


@app.exception_handler(NotAuthenticated)
async def not_authenticated_handler(request: Request, exc: NotAuthenticated):
    return RedirectResponse(url="/login", status_code=303)


@app.get("/")
def root():
    return RedirectResponse(url="/dashboard", status_code=303)
