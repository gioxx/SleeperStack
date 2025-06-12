import os
import requests
import sys
from datetime import datetime

# Optional: load .env file for local testing
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

PORTAINER_URL = os.getenv("PORTAINER_URL", "http://localhost:9000/api")
PORTAINER_API_KEY = os.getenv("PORTAINER_API_KEY")
ENDPOINT_ID = os.getenv("PORTAINER_ENDPOINT_ID")
ACTION = os.getenv("ACTION")
TARGET_LABEL = os.getenv("TARGET_LABEL", "autoshutdown=true")
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"

if not all([PORTAINER_API_KEY, ENDPOINT_ID, ACTION, TARGET_LABEL]):
    print("Missing required environment variables.", file=sys.stderr)
    sys.exit(1)

# Support multiple values (e.g. autoshutdown=night,weekend)
try:
    label_key, label_values_str = TARGET_LABEL.split("=", 1)
    label_values = [v.strip() for v in label_values_str.split(",")]
except ValueError:
    print("TARGET_LABEL must be in the form key=value[,value2,...]", file=sys.stderr)
    sys.exit(1)

HEADERS = {"X-API-Key": PORTAINER_API_KEY}

def log(msg):
    print(f"[{datetime.now()}] {msg}")

def get_target_containers():
    url = f"{PORTAINER_URL}/endpoints/{ENDPOINT_ID}/docker/containers/json?all=true"
    res = requests.get(url, headers=HEADERS)

    if not res.ok:
        log(f"Failed to retrieve containers - Status {res.status_code}")
        log(f"Response text: {res.text}")
        sys.exit(1)

    try:
        containers = res.json()
    except Exception as e:
        log(f"Error parsing JSON response: {e}")
        sys.exit(1)

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

def stop_containers(containers):
    for cid, name, state in containers:
        if state == "exited":
            log(f"Skipping stop: {name or cid} is already stopped.")
            continue
        if DRY_RUN:
            log(f"[DRY RUN] Would stop {name or cid}")
            continue
        url = f"{PORTAINER_URL}/endpoints/{ENDPOINT_ID}/docker/containers/{cid}/stop"
        res = requests.post(url, headers=HEADERS)
        log(f"Stopped {name or cid} - Status {res.status_code}")

def start_containers(containers):
    for cid, name, state in containers:
        if state == "running":
            log(f"Skipping start: {name or cid} is already running.")
            continue
        if DRY_RUN:
            log(f"[DRY RUN] Would start {name or cid}")
            continue
        url = f"{PORTAINER_URL}/endpoints/{ENDPOINT_ID}/docker/containers/{cid}/start"
        res = requests.post(url, headers=HEADERS)
        log(f"Started {name or cid} - Status {res.status_code}")

def main():
    containers = get_target_containers()
    if not containers:
        log(f"No container found with label {TARGET_LABEL}")
        return

    if ACTION == "stop":
        stop_containers(containers)
    elif ACTION == "start":
        start_containers(containers)
    else:
        log(f"Unknown ACTION: {ACTION}")
        sys.exit(1)

if __name__ == "__main__":
    main()
