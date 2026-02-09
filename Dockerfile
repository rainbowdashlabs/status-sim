FROM python:3.14-slim

WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser

ENV PIPENV_VENV_IN_PROJECT=true

COPY Pipfile Pipfile.lock /app/

RUN pip install --no-cache-dir pipenv && \
    pipenv sync

COPY src/ ./src/

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["pipenv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
