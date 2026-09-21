FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --default-timeout=120 --retries 8 --no-cache-dir \
    -r /app/requirements.txt fastapi uvicorn azure-storage-blob
COPY . /app
ENV PYTHONPATH=/app
ENV PORT=8080
EXPOSE 8080
CMD ["uvicorn", "services.foundry_runtime.main:app", "--host", "0.0.0.0", "--port", "8080"]
