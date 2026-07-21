import json
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.crypto import decrypt
from app.models import Rule, RunHistory
from portainer_client import (
    PortainerAPIError,
    get_target_containers,
    start_containers,
    stop_containers,
)


def _job_id(rule_id):
    return f"rule-{rule_id}"


class SchedulerService:
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.scheduler = BackgroundScheduler()

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
        session = self.session_factory()
        try:
            for rule in session.query(Rule).filter_by(enabled=True).all():
                self.add_job(rule)
        finally:
            session.close()

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def add_job(self, rule):
        self.scheduler.add_job(
            self.run_rule,
            trigger=CronTrigger.from_crontab(rule.cron_expression),
            id=_job_id(rule.id),
            args=[rule.id],
            replace_existing=True,
        )

    def remove_job(self, rule_id):
        job_id = _job_id(rule_id)
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

    def run_rule(self, rule_id):
        session = self.session_factory()
        try:
            rule = session.get(Rule, rule_id)
            if rule is None or not rule.enabled:
                return

            endpoint = rule.endpoint
            history = RunHistory(rule_id=rule.id, status="running", dry_run=False)
            session.add(history)
            session.commit()

            try:
                label_key, label_values_str = rule.target_label.split("=", 1)
                label_values = [v.strip() for v in label_values_str.split(",")]
                api_key = decrypt(endpoint.api_key_encrypted)

                containers = get_target_containers(
                    endpoint.portainer_url,
                    api_key,
                    endpoint.endpoint_id,
                    label_key,
                    label_values,
                )

                if rule.action == "stop":
                    results = stop_containers(
                        endpoint.portainer_url, api_key, endpoint.endpoint_id, containers
                    )
                else:
                    results = start_containers(
                        endpoint.portainer_url, api_key, endpoint.endpoint_id, containers
                    )

                history.status = "success"
                history.detail_json = json.dumps({"results": results})
            except PortainerAPIError as e:
                history.status = "error"
                history.detail_json = json.dumps({"error": str(e)})

            history.finished_at = datetime.now(timezone.utc)
            session.commit()
        finally:
            session.close()
