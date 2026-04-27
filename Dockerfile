FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    pandas \
    numpy \
    scipy \
    statsmodels \
    sqlalchemy \
    psycopg2-binary \
    pydantic

COPY api/ api/
COPY src/ src/

EXPOSE 8000

CMD ["sh", "-c", "python src/simulate.py && uvicorn api.main:app --host 0.0.0.0 --port 8000"]