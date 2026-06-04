FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r backend/requirements.txt \
    && python scripts/generate_demo_data.py
EXPOSE 8787
# Without a mounted analysis directory the app serves the bundled demo dataset.
# For real data: mount processed outputs read-only and set
#   RLE_ANALYSIS_DATA_DIR=/analysis
# Honors $PORT (Render/Cloud Run/Heroku inject it); defaults to 8787 locally.
CMD ["sh", "-c", "uvicorn backend.fastapi_app:app --host 0.0.0.0 --port ${PORT:-8787}"]
