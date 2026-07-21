#!/bin/sh
set -e

if [ "$MODE" = "oneshot" ]; then
  exec python main.py
else
  exec uvicorn app.main:app --host 0.0.0.0 --port 8000
fi
