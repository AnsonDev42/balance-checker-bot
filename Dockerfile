FROM python:3.12.1-slim

LABEL authors="AnsonDev42"
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3-dev libpq-dev gcc\
    && rm -rf /var/lib/apt/lists/*

RUN pip install pipx
RUN pipx install poetry
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app
COPY pyproject.toml ../poetry.lock* /app/

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY balance_checker ./balance_checker
WORKDIR /app/balance_checker

CMD ["python", "main.py"]
EXPOSE 8000
