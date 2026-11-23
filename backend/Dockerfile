# syntax=docker/dockerfile:1

# ---------------------------------------------------------------- base -------
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# --------------------------------------------------------- development -------
FROM base AS development
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt
COPY . .
EXPOSE 8000
CMD ["sh", "/app/scripts/start-dev.sh"]

# ---------------------------------------------------------- production -------
FROM base AS production
RUN useradd --create-home --uid 1000 app
COPY --chown=app:app . .
USER app
EXPOSE 8000
CMD ["sh", "/app/scripts/start-prod.sh"]
