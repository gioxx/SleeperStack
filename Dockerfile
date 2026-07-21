FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get upgrade -y && \
	apt-get install -y --no-install-recommends build-essential libffi-dev && \
	pip install --no-cache-dir -r requirements.txt && \
	apt-get purge -y --auto-remove build-essential libffi-dev && \
	apt-get clean && rm -rf /var/lib/apt/lists/*

COPY main.py portainer_client.py entrypoint.sh .
COPY app/ app/

RUN mkdir -p /data && chmod +x entrypoint.sh

EXPOSE 8000
VOLUME ["/data"]

ENTRYPOINT ["./entrypoint.sh"]
