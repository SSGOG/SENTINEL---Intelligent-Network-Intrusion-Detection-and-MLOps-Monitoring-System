# Multi‑stage Dockerfile for SENTINEL FastAPI service
# ------------------------------------------------------
# Builder stage – sets up the Python environment and installs deps
FROM python:3.11-slim AS builder
WORKDIR /app

# Install build‑essential for any compiled wheels (e.g., xgboost)
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Copy only the requirements to leverage layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code and model artifacts
COPY src/ ./src/
COPY models/ ./models/
COPY data/processed/feature_schema.json ./data/processed/
COPY reports/metrics/model_selection_manifest.json ./reports/metrics/

# Final runtime image – minimal
FROM python:3.11-slim AS runtime
WORKDIR /app

# Copy only the installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application files
COPY --from=builder /app/src ./src
COPY --from=builder /app/models ./models
COPY --from=builder /app/data/processed ./data/processed
COPY --from=builder /app/reports/metrics ./reports/metrics

# Expose the FastAPI port
EXPOSE 8000

# Set non‑root user for security (optional but recommended)
RUN groupadd -r appgroup && useradd -r -g appgroup appuser && chown -R appuser:appgroup /app
USER appuser

# Entrypoint – start the API
ENTRYPOINT ["uvicorn", "src.sentinel.api:app", "--host", "0.0.0.0", "--port", "8000"]
