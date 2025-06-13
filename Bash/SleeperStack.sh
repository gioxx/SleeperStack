#!/bin/bash
# SleeperStack launcher script
# Usage:
#   ./SleeperStack.sh --action [start|stop] --group <label> --endpoint <id> \
#                     --profile <profile> [--dry-run]
#   ./SleeperStack.sh --update-image         # pull latest image and exit

IMAGE_NAME="gfsolone/sleeperstack:latest"
SECRETS_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.secrets"

# Load secrets
if [[ -f "$SECRETS_FILE" ]]; then
  source "$SECRETS_FILE"
else
  echo "Missing .secrets file ($SECRETS_FILE)"
  exit 1
fi

# Default values
DRY_RUN=false
UPDATE_ONLY=false

# Parse arguments
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --action)   ACTION="$2";           shift 2 ;;
    --group)    LABEL_GROUP="$2";      shift 2 ;;
    --endpoint) ENDPOINT_ID="$2";      shift 2 ;;
    --profile)  API_PROFILE="$2";      shift 2 ;;
    --dry-run)  DRY_RUN=true;          shift   ;;
    --update-image) UPDATE_ONLY=true;  shift   ;;
    -h|--help)
      cat <<EOF
Usage:
  $0 --action [start|stop] --group <label> --endpoint <id> --profile <profile> [--dry-run]
  $0 --update-image        # pulls latest $IMAGE_NAME and exits
EOF
      exit 0 ;;
    *)  echo "Unknown parameter: $1"; exit 1 ;;
  esac
done

# If only image update is requested
if $UPDATE_ONLY; then
  docker pull "$IMAGE_NAME"
  exit $?
fi

# Validate inputs
if [[ -z "$ACTION" || -z "$LABEL_GROUP" || -z "$ENDPOINT_ID" || -z "$API_PROFILE" ]]; then
  echo "Missing required arguments. Run with --help for usage."
  exit 1
fi
[[ "$ACTION" =~ ^(start|stop)$ ]] || { echo "Invalid --action"; exit 1; }

# Lookup API key and URL from profile
PROFILE_UPPER="${API_PROFILE^^}"
API_KEY_VAR="PORTAINER_API_KEY_${PROFILE_UPPER}"
URL_VAR="PORTAINER_URL_${PROFILE_UPPER}"
PORTAINER_API_KEY="${!API_KEY_VAR}"
PORTAINER_URL="${!URL_VAR}"

if [[ -z "$PORTAINER_API_KEY" || -z "$PORTAINER_URL" ]]; then
  echo "Missing API key or URL for profile '$API_PROFILE'"
  exit 1
fi

# Pull image only if not already present
if ! docker image inspect "$IMAGE_NAME" &>/dev/null; then
  echo "Image not found locally - pulling once"
  docker pull "$IMAGE_NAME" || exit 1
fi

# Run container
docker run --rm \
  -e PORTAINER_URL="$PORTAINER_URL" \
  -e PORTAINER_API_KEY="$PORTAINER_API_KEY" \
  -e PORTAINER_ENDPOINT_ID="$ENDPOINT_ID" \
  -e TARGET_LABEL="autoshutdown=${LABEL_GROUP}" \
  -e ACTION="$ACTION" \
  $( $DRY_RUN && echo "-e DRY_RUN=true" ) \
  "$IMAGE_NAME"
