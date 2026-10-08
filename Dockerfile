FROM python:3.12-slim

# Install system C-libraries required by GDAL, GEOS, and PyProj
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install uv from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies deterministically
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-cache

# Copy project source files
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./alembic.ini
COPY README.md ./README.md

# Place venv on PATH
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

