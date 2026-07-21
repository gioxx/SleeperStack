import os
import sys

# Optional: load .env file for local testing
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from portainer_client import (
    PortainerAPIError,
    get_target_containers,
    log,
    start_containers,
    stop_containers,
)

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


def main():
    try:
        containers = get_target_containers(
            PORTAINER_URL, PORTAINER_API_KEY, ENDPOINT_ID, label_key, label_values
        )
    except PortainerAPIError:
        sys.exit(1)

    if not containers:
        log(f"No container found with label {TARGET_LABEL}")
        return

    if ACTION == "stop":
        stop_containers(PORTAINER_URL, PORTAINER_API_KEY, ENDPOINT_ID, containers, DRY_RUN)
    elif ACTION == "start":
        start_containers(PORTAINER_URL, PORTAINER_API_KEY, ENDPOINT_ID, containers, DRY_RUN)
    else:
        log(f"Unknown ACTION: {ACTION}")
        sys.exit(1)


if __name__ == "__main__":
    main()
