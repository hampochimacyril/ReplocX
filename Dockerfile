# Multi-stage build: a Node stage compiles the React/Vite frontend to static
# assets, and the final Python image installs the backend and serves both the
# /api/v1 API and the built assets from frontend/dist.

# --- Stage 1: build the frontend ---
FROM node:22-slim AS web
WORKDIR /web/frontend
# Install with the committed lockfile first for reproducible, cacheable layers.
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Python runtime ---
FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY . /app
# Bring in the compiled static assets. frontend/dist is .dockerignored from the
# host context, so the only dist that ships is the one built in the web stage.
COPY --from=web /web/frontend/dist /app/frontend/dist
RUN python scripts/generate_demo_data.py
EXPOSE 8787
# Without a mounted analysis directory the app serves the bundled demo dataset.
# For real data: mount processed outputs read-only and set
#   RLE_ANALYSIS_DATA_DIR=/analysis
# Honors $PORT (Render/Cloud Run/Heroku inject it); defaults to 8787 locally.
CMD ["sh", "-c", "uvicorn backend.fastapi_app:app --host 0.0.0.0 --port ${PORT:-8787}"]
