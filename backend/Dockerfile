FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN addgroup --system elite \
    && adduser --system --ingroup elite --home /app elite

COPY --chown=elite:elite alembic.ini .
COPY --chown=elite:elite migrations ./migrations
COPY --chown=elite:elite app ./app

RUN mkdir -p /app/uploads \
    && chown -R elite:elite /app/uploads
VOLUME ["/app/uploads"]

USER elite

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
