FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system flaxon && adduser --system --ingroup flaxon flaxon

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY examples ./examples

RUN pip install --no-cache-dir ".[standard]"

USER flaxon
EXPOSE 8000

CMD ["flaxon", "run", "examples.hello_api.app:app", "--host", "0.0.0.0", "--port", "8000"]
