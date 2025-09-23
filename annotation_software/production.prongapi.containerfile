FROM python:3.13-slim-bookworm as build-stage

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libpq-dev \
    bash \
    python3-venv \
    gcc \
    build-essential \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /venv

COPY ./requirements.txt requirements.txt

COPY ./crop_generator /venv/crop_generator

RUN python3 -m venv --clear api_env && \
    /bin/bash -c "source api_env/bin/activate && python -m pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt"

FROM python:3.13-slim as production-stage

COPY --from=build-stage /venv/api_env /venv/api_env

COPY --from=build-stage /venv/crop_generator /venv/crop_generator

ENV PATH="/venv/api_env/bin:$PATH"

WORKDIR /app

COPY ./generator_api .

CMD ["gunicorn", "-w", "8", "-b", "0.0.0.0:8000", "cg_api:app"]