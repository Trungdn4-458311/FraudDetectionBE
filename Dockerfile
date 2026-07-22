# Reproducible container for the fraud-detection demo.
#   docker build -t fraud-demo .
#   docker run --rm -p 8501:8501 fraud-demo          # Streamlit review queue (default)
#   docker run --rm -p 8000:8000 -e PORT=8000 fraud-demo api   # FastAPI scorer (/docs)
# Hugging Face "Docker" Space: set app_port: 7860 and PORT=7860.
FROM python:3.11-slim

WORKDIR /app
COPY deployment/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY deployment/ ./
RUN chmod +x entrypoint.sh

ENV PORT=8501
EXPOSE 8501 8000
ENTRYPOINT ["./entrypoint.sh"]
