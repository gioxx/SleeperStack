FROM python:3.15.0a5-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get upgrade -y && apt-get clean && \
	pip install --no-cache-dir -r requirements.txt

COPY main.py .

CMD ["python", "main.py"]
