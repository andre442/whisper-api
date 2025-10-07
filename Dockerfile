# Dockerfile para o serviço Whisper - Otimizado para Railway
FROM python:3.10-slim

# Instalar dependências de SO (ffmpeg para Whisper)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements primeiro (melhor cache de layers)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código do serviço
COPY transcribe_api.py .

# Expor porta (Railway detecta automaticamente)
EXPOSE 5005

# Variáveis de ambiente com valores padrão
ENV MODEL_SIZE=base
ENV PORT=5005
ENV PYTHONUNBUFFERED=1

# Health check para Railway
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:5005/health')" || exit 1

# Usar gunicorn para produção (melhor performance)
CMD gunicorn --bind 0.0.0.0:${PORT} --workers 1 --timeout 120 --log-level info transcribe_api:app
