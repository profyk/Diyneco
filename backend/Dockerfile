# Diyneco API and worker image. The same image runs both:
#   API:    the default CMD
#   Worker: python -m app.worker
FROM python:3.12-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY scripts/check_migrations.py ./scripts/check_migrations.py

FROM python:3.12-slim
RUN useradd --system --uid 10001 --home /app diyneco
WORKDIR /app
COPY --from=build --chown=diyneco:diyneco /app /app
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
USER diyneco
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=2).status == 200 else 1)"
# Client IPs (rate limits, audit) come from X-Forwarded-For only when the request arrives from a
# trusted proxy: set FORWARDED_ALLOW_IPS to the load balancer's address range per environment.
# Never "*" on a container that is reachable directly.
ENV FORWARDED_ALLOW_IPS=127.0.0.1
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
