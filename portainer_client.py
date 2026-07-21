from datetime import datetime

import requests


class PortainerAPIError(Exception):
    pass


def log(msg):
    print(f"[{datetime.now()}] {msg}")


def get_target_containers(portainer_url, api_key, endpoint_id, label_key, label_values):
    headers = {"X-API-Key": api_key}
    url = f"{portainer_url}/endpoints/{endpoint_id}/docker/containers/json?all=true"
    res = requests.get(url, headers=headers)

    if not res.ok:
        log(f"Failed to retrieve containers - Status {res.status_code}")
        log(f"Response text: {res.text}")
        raise PortainerAPIError(f"Failed to retrieve containers - Status {res.status_code}")

    try:
        containers = res.json()
    except Exception as e:
        raise PortainerAPIError(f"Error parsing JSON response: {e}")

    targets = []
    for container in containers:
        labels = container.get("Labels", {})
        label_val = labels.get(label_key)
        if label_val and label_val in label_values:
            container_id = container.get("Id")
            name = container.get("Names", [None])[0]
            state = container.get("State")
            if container_id:
                targets.append((container_id, name, state))
    return targets


def get_all_containers(portainer_url, api_key, endpoint_id):
    headers = {"X-API-Key": api_key}
    url = f"{portainer_url}/endpoints/{endpoint_id}/docker/containers/json?all=true"
    res = requests.get(url, headers=headers)

    if not res.ok:
        log(f"Failed to retrieve containers - Status {res.status_code}")
        log(f"Response text: {res.text}")
        raise PortainerAPIError(f"Failed to retrieve containers - Status {res.status_code}")

    try:
        return res.json()
    except Exception as e:
        raise PortainerAPIError(f"Error parsing JSON response: {e}")


def stop_containers(portainer_url, api_key, endpoint_id, containers, dry_run=False):
    headers = {"X-API-Key": api_key}
    results = []
    for cid, name, state in containers:
        if state == "exited":
            log(f"Skipping stop: {name or cid} is already stopped.")
            results.append((cid, name, "skipped"))
            continue
        if dry_run:
            log(f"[DRY RUN] Would stop {name or cid}")
            results.append((cid, name, "dry_run"))
            continue
        url = f"{portainer_url}/endpoints/{endpoint_id}/docker/containers/{cid}/stop"
        res = requests.post(url, headers=headers)
        log(f"Stopped {name or cid} - Status {res.status_code}")
        results.append((cid, name, "stopped" if res.ok else f"error_{res.status_code}"))
    return results


def start_containers(portainer_url, api_key, endpoint_id, containers, dry_run=False):
    headers = {"X-API-Key": api_key}
    results = []
    for cid, name, state in containers:
        if state == "running":
            log(f"Skipping start: {name or cid} is already running.")
            results.append((cid, name, "skipped"))
            continue
        if dry_run:
            log(f"[DRY RUN] Would start {name or cid}")
            results.append((cid, name, "dry_run"))
            continue
        url = f"{portainer_url}/endpoints/{endpoint_id}/docker/containers/{cid}/start"
        res = requests.post(url, headers=headers)
        log(f"Started {name or cid} - Status {res.status_code}")
        results.append((cid, name, "started" if res.ok else f"error_{res.status_code}"))
    return results
