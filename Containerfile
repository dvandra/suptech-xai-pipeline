# Unified application image for SupTech-XAI.
#
# One image runs every component - the FMR mock, the metrics API, the Streamlit
# dashboard, and the batch pipeline - selected by overriding the container
# command. Built to run under OpenShift's restricted SCC: no fixed root UID,
# the app tree is group-0 owned and group-writable so an arbitrary assigned UID
# can read/write it.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOME=/app \
    HF_HOME=/app/.cache \
    STREAMLIT_SERVER_HEADLESS=true

WORKDIR /app

# Core dependencies + Streamlit (the heavy ML/LLM libs are optional; the code
# falls back gracefully when they are absent, keeping the image small).
COPY requirements.txt .
RUN pip install --no-cache-dir \
    duckdb numpy fastapi uvicorn pydantic requests streamlit

COPY . .

# OpenShift compatibility: arbitrary UID in the root (0) group.
RUN mkdir -p /app/data /app/.cache \
    && chgrp -R 0 /app \
    && chmod -R g=u /app

USER 1001

EXPOSE 8000 8001 8501

# Default: run the FMR mock. Override `command`/`args` for other components.
CMD ["uvicorn", "metadata_registry.fmr_mock_api:app", "--host", "0.0.0.0", "--port", "8000"]
