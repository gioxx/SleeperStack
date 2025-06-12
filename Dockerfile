FROM python:3.12-slim-bullseye

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get upgrade -y && apt-get clean && \
	pip install --no-cache-dir -r requirements.txt

COPY main.py .

CMD ["python", "main.py"]
