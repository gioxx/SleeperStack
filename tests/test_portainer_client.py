import pytest

from portainer_client import (
    PortainerAPIError,
    get_all_containers,
    get_target_containers,
    start_containers,
    stop_containers,
)

BASE = "http://portainer.local/api"
ENDPOINT_ID = "2"


def containers_url():
    return f"{BASE}/endpoints/{ENDPOINT_ID}/docker/containers/json?all=true"


def test_get_target_containers_filters_by_label(requests_mock):
    requests_mock.get(
        containers_url(),
        json=[
            {
                "Id": "abc",
                "Names": ["/night-app"],
                "State": "running",
                "Labels": {"autoshutdown": "night"},
            },
            {
                "Id": "def",
                "Names": ["/other-app"],
                "State": "running",
                "Labels": {"autoshutdown": "weekend"},
            },
        ],
    )

    result = get_target_containers(BASE, "key", ENDPOINT_ID, "autoshutdown", ["night"])

    assert result == [("abc", "/night-app", "running")]


def test_get_target_containers_raises_on_error_status(requests_mock):
    requests_mock.get(containers_url(), status_code=401, text="unauthorized")

    with pytest.raises(PortainerAPIError):
        get_target_containers(BASE, "key", ENDPOINT_ID, "autoshutdown", ["night"])


def test_get_all_containers_returns_full_list(requests_mock):
    payload = [
        {"Id": "abc", "Names": ["/a"], "State": "running", "Labels": {}},
        {"Id": "def", "Names": ["/b"], "State": "exited", "Labels": {"autoshutdown": "night"}},
    ]
    requests_mock.get(containers_url(), json=payload)

    result = get_all_containers(BASE, "key", ENDPOINT_ID)

    assert result == payload


def test_stop_containers_skips_already_exited(requests_mock):
    result = stop_containers(
        BASE, "key", ENDPOINT_ID, [("abc", "/app", "exited")], dry_run=False
    )

    assert result == [("abc", "/app", "skipped")]
    assert not requests_mock.request_history


def test_stop_containers_dry_run_does_not_call_api(requests_mock):
    result = stop_containers(
        BASE, "key", ENDPOINT_ID, [("abc", "/app", "running")], dry_run=True
    )

    assert result == [("abc", "/app", "dry_run")]
    assert not requests_mock.request_history


def test_stop_containers_calls_stop_endpoint(requests_mock):
    requests_mock.post(f"{BASE}/endpoints/{ENDPOINT_ID}/docker/containers/abc/stop", status_code=204)

    result = stop_containers(
        BASE, "key", ENDPOINT_ID, [("abc", "/app", "running")], dry_run=False
    )

    assert result == [("abc", "/app", "stopped")]


def test_start_containers_skips_already_running(requests_mock):
    result = start_containers(
        BASE, "key", ENDPOINT_ID, [("abc", "/app", "running")], dry_run=False
    )

    assert result == [("abc", "/app", "skipped")]
    assert not requests_mock.request_history


def test_start_containers_calls_start_endpoint(requests_mock):
    requests_mock.post(f"{BASE}/endpoints/{ENDPOINT_ID}/docker/containers/abc/start", status_code=204)

    result = start_containers(
        BASE, "key", ENDPOINT_ID, [("abc", "/app", "exited")], dry_run=False
    )

    assert result == [("abc", "/app", "started")]
