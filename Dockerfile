# --- المرحلة 1: بناء الواجهة (Node) ---
FROM node:22-alpine AS frontend-build
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# --- المرحلة 2: وقت التشغيل (Python) ---
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8001

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --timeout 60 --retries 10 --prefer-binary -r /tmp/requirements.txt

COPY backend/ backend/
COPY serve.py .
COPY --from=frontend-build /build/dist frontend/dist

EXPOSE 8001
CMD ["sh", "-c", "python -m uvicorn serve:app --host 0.0.0.0 --port $PORT"]