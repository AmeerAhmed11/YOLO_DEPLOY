FROM python:3.11-slim

WORKDIR /app

COPY proxy/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY proxy/ ./proxy/
COPY static/ ./static/

ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "proxy.server:app", "--host", "0.0.0.0", "--port", "8080"]
