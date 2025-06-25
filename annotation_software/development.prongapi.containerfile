FROM python:3.13-slim-bookworm

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

COPY requirements.txt ./

COPY ../crop_generator /venv/crop_generator

RUN python3 -m venv --clear api_env && \
    /bin/bash -c "source api_env/bin/activate && python -m pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt"

EXPOSE 5000

CMD ["/bin/bash", "-c", "source  api_env/bin/activate && python -u cg_api.py"]