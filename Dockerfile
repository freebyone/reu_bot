# FROM python:3.11-slim

WORKDIR /app

# Отдельный слой для зависимостей
COPY requirements/prod.txt .
RUN pip install --no-cache-dir -r prod.txt

# Копируем только необходимое
COPY bot ./bot
COPY utils ./utils
COPY services ./services
COPY database ./database
COPY .env.prod .env

CMD ["python", "-m", "bot"]