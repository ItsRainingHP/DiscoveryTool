FROM node:25-bookworm-slim AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
COPY RFP_TUTORIAL.md /app/RFP_TUTORIAL.md
RUN npm run build


FROM python:3.14-slim AS runtime

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend/ /app/backend/
COPY examples/ /app/examples/
COPY --from=frontend-builder /app/frontend/out /app/frontend/out

ENV PYTHONPATH=/app/backend
ENV FRONTEND_DIST_DIR=/app/frontend/out
ENV PORT=8000

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--app-dir", "/app/backend", "--host", "0.0.0.0", "--port", "8000"]
