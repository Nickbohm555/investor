FROM python:3.12-slim

ARG SUPERCRONIC_VERSION=v0.2.43

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl gettext-base tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSLo /usr/local/bin/supercronic "https://github.com/aptible/supercronic/releases/download/${SUPERCRONIC_VERSION}/supercronic-linux-amd64" \
    && chmod +x /usr/local/bin/supercronic

COPY pyproject.toml README.md alembic.ini ./
COPY app ./app
COPY ops ./ops

RUN pip install --no-cache-dir -e .

EXPOSE 8000

HEALTHCHECK CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["/app/ops/docker/start-app-runtime.sh"]
