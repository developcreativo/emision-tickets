FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev git \
    && rm -rf /var/lib/apt/lists/*

# Permite seleccionar el archivo de requirements en build (prod por defecto)
ARG REQUIREMENTS_FILE=requirements.txt

# Copiamos ambos archivos para poder elegir en build
COPY requirements.txt /app/requirements.txt
COPY requirements-dev.txt /app/requirements-dev.txt

RUN pip install --no-cache-dir -r ${REQUIREMENTS_FILE}

COPY . /app

EXPOSE 8000
