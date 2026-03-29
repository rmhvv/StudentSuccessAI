FROM python:3.12-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

# Устанавливаем все Python пакеты (включая plotly)
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
    plotly

EXPOSE 8000 8501

CMD ["echo", "Use docker-compose to start services"]