FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    pandas \
    numpy \
    scipy \
    statsmodels \
    pydantic

COPY api/ api/

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]