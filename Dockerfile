FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install pycountry gTTS

COPY . .

EXPOSE 8000 8501

CMD ["uvicorn", "src.backend.server:app", "--host", "0.0.0.0", "--port", "8000"]
