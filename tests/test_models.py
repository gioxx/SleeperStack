from app.db import Base, init_db, make_engine
from app.models import Endpoint, Rule, RunHistory, User
from sqlalchemy.orm import sessionmaker


def make_session():
    engine = make_engine(db_path=":memory:")
    init_db(bind_engine=engine)
    return sessionmaker(bind=engine)()


def test_init_db_creates_all_tables():
    engine = make_engine(db_path=":memory:")
    init_db(bind_engine=engine)

    table_names = set(Base.metadata.tables.keys())
    assert table_names == {"users", "endpoints", "rules", "run_history"}


def test_create_endpoint_and_rule():
    session = make_session()

    endpoint = Endpoint(
        name="lab",
        portainer_url="http://portainer.local/api",
        api_key_encrypted="enc:abc",
        endpoint_id="2",
    )
    session.add(endpoint)
    session.commit()

    rule = Rule(
        endpoint_id=endpoint.id,
        target_label="autoshutdown=night",
        action="stop",
        cron_expression="0 22 * * *",
    )
    session.add(rule)
    session.commit()

    fetched = session.get(Rule, rule.id)
    assert fetched.endpoint.name == "lab"
    assert fetched.enabled is True


def test_run_history_allows_null_rule_id_for_manual_actions():
    session = make_session()

    history = RunHistory(rule_id=None, status="success", dry_run=False, detail_json="{}")
    session.add(history)
    session.commit()

    fetched = session.get(RunHistory, history.id)
    assert fetched.rule_id is None


def test_user_unique_username():
    session = make_session()

    session.add(User(username="admin", password_hash="hash", role="admin"))
    session.commit()

    fetched = session.query(User).filter_by(username="admin").one()
    assert fetched.role == "admin"
