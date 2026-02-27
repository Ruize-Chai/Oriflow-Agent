FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# install system deps (minimal) and python deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# copy project
COPY . /app

# create non-root user for safety
RUN groupadd -r oriflow && useradd -r -g oriflow oriflow && chown -R oriflow:oriflow /app
USER oriflow

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
