# Используем официальное изображение Python
FROM python:3.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY data_collector/requirements.txt /app/requirements.txt

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY data_collector /app

# Указываем переменные окружения (из .env)
COPY common/.env /app/common/.env

# Копируем папку common
COPY common /app/common

# Устанавливаем рабочую директорию
WORKDIR /app

# Запуск приложения
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
