FROM python:3.7
ENV PYTHONUNBUFFERED 1
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8005
CMD ["bash", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8005"]