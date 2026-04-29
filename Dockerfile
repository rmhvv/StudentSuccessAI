FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN pip install --no-cache-dir \
    psycopg2-binary \
    pandas \
    scikit-learn \
    joblib \
    fastapi \
    uvicorn \
    pydantic \
    python-multipart \
    faker \
    streamlit \
    requests \
    plotly \
    duckdb

EXPOSE 8000 8501

# Однострочный CMD — самый надёжный вариант для Docker
CMD sh -c "echo '=== Starting FastAPI Backend ===' && python -m uvicorn main:app --host 0.0.0.0 --port \$PORT & echo '=== Starting Streamlit Frontend ===' && python -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless=true"