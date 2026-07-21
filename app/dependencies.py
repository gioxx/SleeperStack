from fastapi import Request

from app.scheduler import SchedulerService


def get_scheduler(request: Request) -> SchedulerService:
    return request.app.state.scheduler
