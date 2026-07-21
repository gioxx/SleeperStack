FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get upgrade -y && apt-get clean && \
	pip install --no-cache-dir -r requirements.txt

COPY main.py portainer_client.py entrypoint.sh .
COPY app/ app/

RUN mkdir -p /data && chmod +x entrypoint.sh

EXPOSE 8000
VOLUME ["/data"]

ENTRYPOINT ["./entrypoint.sh"]
