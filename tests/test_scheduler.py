import json

import pytest
from sqlalchemy.orm import sessionmaker

from app.crypto import encrypt
from app.db import init_db, make_engine
from app.models import Endpoint, Rule, RunHistory
from app.scheduler import SchedulerService

BASE = "http://portainer.local/api"
ENDPOINT_ID = "2"


@pytest.fixture(autouse=True)
def secret_key(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-value")


def make_session_factory():
    engine = make_engine(db_path=":memory:")
    init_db(bind_engine=engine)
    return sessionmaker(bind=engine)


def create_rule(session_factory, cron="0 22 * * *", action="stop", enabled=True):
    session = session_factory()
    endpoint = Endpoint(
        name="lab",
        portainer_url=BASE,
        api_key_encrypted=encrypt("secret-key"),
        endpoint_id=ENDPOINT_ID,
    )
    session.add(endpoint)
    session.commit()

    rule = Rule(
        endpoint_id=endpoint.id,
        target_label="autoshutdown=night",
        action=action,
        cron_expression=cron,
        enabled=enabled,
    )
    session.add(rule)
    session.commit()
    rule_id = rule.id
    session.close()
    return rule_id


def containers_url():
    return f"{BASE}/endpoints/{ENDPOINT_ID}/docker/containers/json?all=true"


def test_run_rule_stops_matching_containers_and_logs_success(requests_mock):
    session_factory = make_session_factory()
    rule_id = create_rule(session_factory, action="stop")

    requests_mock.get(
        containers_url(),
        json=[{"Id": "abc", "Names": ["/night-app"], "State": "running", "Labels": {"autoshutdown": "night"}}],
    )
    requests_mock.post(f"{BASE}/endpoints/{ENDPOINT_ID}/docker/containers/abc/stop", status_code=204)

    service = SchedulerService(session_factory)
    service.run_rule(rule_id)

    session = session_factory()
    history = session.query(RunHistory).filter_by(rule_id=rule_id).one()
    assert history.status == "success"
    assert json.loads(history.detail_json)["results"] == [["abc", "/night-app", "stopped"]]


def test_run_rule_logs_error_on_api_failure(requests_mock):
    session_factory = make_session_factory()
    rule_id = create_rule(session_factory, action="stop")

    requests_mock.get(containers_url(), status_code=401, text="unauthorized")

    service = SchedulerService(session_factory)
    service.run_rule(rule_id)

    session = session_factory()
    history = session.query(RunHistory).filter_by(rule_id=rule_id).one()
    assert history.status == "error"
    assert "Failed to retrieve containers" in json.loads(history.detail_json)["error"]


def test_run_rule_skips_disabled_rule(requests_mock):
    session_factory = make_session_factory()
    rule_id = create_rule(session_factory, enabled=False)

    service = SchedulerService(session_factory)
    service.run_rule(rule_id)

    session = session_factory()
    assert session.query(RunHistory).filter_by(rule_id=rule_id).count() == 0
    assert not requests_mock.request_history


def test_add_job_registers_job_and_remove_job_unregisters_it():
    session_factory = make_session_factory()
    rule_id = create_rule(session_factory, cron="0 22 * * *")

    session = session_factory()
    rule = session.get(Rule, rule_id)

    service = SchedulerService(session_factory)
    service.add_job(rule)
    assert service.scheduler.get_job(f"rule-{rule_id}") is not None

    service.remove_job(rule_id)
    assert service.scheduler.get_job(f"rule-{rule_id}") is None


def test_start_loads_only_enabled_rules():
    session_factory = make_session_factory()
    enabled_id = create_rule(session_factory, cron="0 22 * * *", enabled=True)
    disabled_id = create_rule(session_factory, cron="0 7 * * *", enabled=False)

    service = SchedulerService(session_factory)
    service.start()

    assert service.scheduler.get_job(f"rule-{enabled_id}") is not None
    assert service.scheduler.get_job(f"rule-{disabled_id}") is None

    service.shutdown()
