FROM nixos/nix:latest AS frontend

WORKDIR /build/
RUN nix-channel --update
COPY shell.nix .

COPY frontend/package*.json /build
RUN nix-shell --run "npm ci"
COPY frontend/ .
RUN nix-shell --run "npm run build"


# ---------- Python runtime stage ----------
FROM python:3.14-slim

WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser

ENV PIPENV_VENV_IN_PROJECT=true

COPY Pipfile Pipfile.lock /app/

RUN pip install --no-cache-dir pipenv && \
    pipenv sync

COPY src/ ./src/
# Copy built frontend artifacts into Python source tree
COPY --from=frontend /build/dist /app/src/frontend_dist

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["pipenv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "src"]
