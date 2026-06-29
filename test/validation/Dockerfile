# Use an official Python runtime as a parent image
FROM python:3.7

# Set environment variables
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app will run on
EXPOSE 8004

# Define the command to run on container start
# CMD ["python", "manage.py", "makemigrations"]
# CMD ["python", "manage.py", "migrate"]

# Default command to run your Django app
CMD ["bash", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8004"]