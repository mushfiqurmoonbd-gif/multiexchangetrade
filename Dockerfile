# Placeholder Dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8501
# Render provides $PORT; default to 8501 locally
CMD ["sh","-c","python -m streamlit run app.py --server.port ${PORT:-8501} --server.address 0.0.0.0 --server.headless true"]
