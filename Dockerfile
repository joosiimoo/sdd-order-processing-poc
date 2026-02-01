FROM python:3.10-slim

WORKDIR /app

COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt uvicorn

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
