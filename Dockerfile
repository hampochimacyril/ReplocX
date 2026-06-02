FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r backend/requirements.txt
EXPOSE 8787
# Mount analytical outputs read-only at /analysis and set RLE_ANALYSIS_DATA_DIR=/analysis.
CMD ["uvicorn", "backend.fastapi_app:app", "--host", "0.0.0.0", "--port", "8787"]
