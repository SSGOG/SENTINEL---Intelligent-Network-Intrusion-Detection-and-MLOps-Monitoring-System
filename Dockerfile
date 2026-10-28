# ---- Build stage ---------------------------------------------------------
FROM python:3.11-slim AS builder

# System packages needed at build time
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install only the dependencies used by the serving container
COPY requirements-runtime.txt .
RUN pip install --no-cache-dir -r requirements-runtime.txt

# Copy source code and all required data/report assets
COPY src/ ./src/
COPY models/ ./models/
COPY data/processed/feature_schema.json ./data/processed/feature_schema.json
COPY data/sample/ ./data/sample/
COPY reports/ ./reports/
COPY docs/ ./docs/

# ---- Runtime stage --------------------------------------------------------
FROM python:3.11-slim AS runtime

# Create a non-root user for security
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r appgroup \
    && useradd -r -g appgroup appuser

WORKDIR /app

# Copy only the needed files from the builder
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app/src ./src
COPY --from=builder /app/models ./models
COPY --from=builder /app/data/processed/feature_schema.json ./data/processed/feature_schema.json
COPY --from=builder /app/data/sample ./data/sample
COPY --from=builder /app/reports ./reports
COPY --from=builder /app/docs ./docs
COPY --chmod=755 start.sh ./start.sh

# Switch to non-root user
USER appuser

# Expose the ports that the container will serve
EXPOSE 8000 8501

# Set a writable HOME for Streamlit (non-root user)
ENV HOME=/tmp

# Start FastAPI and Streamlit together
CMD ["./start.sh"]
