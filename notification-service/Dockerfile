FROM python:3.11-slim
WORKDIR /app
COPY notification-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY notification-service/ .
COPY shared ./shared
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
