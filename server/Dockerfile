FROM ultralytics/ultralytics:latest

WORKDIR /app

# Install server dependencies
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server/app.py .

# Copy model (.pt is portable across GPU architectures, unlike .engine)
COPY best.pt /app/best.pt

ENV MODEL_PATH=/app/best.pt
ENV AIP_HTTP_PORT=8080
EXPOSE 8080

# Run the server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
