FROM python:3.11.5

# установка зависимостей 
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# копирование кода приложения
COPY . /app/

# установка рабочей директории
WORKDIR /app

# команда для запуска приложения
CMD ["streamlit", "run", "main_sqlite.py"]
