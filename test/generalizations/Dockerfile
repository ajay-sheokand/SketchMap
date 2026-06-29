FROM python:3.7-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install system dependencies for pyproj / geopandas / fiona
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    proj-bin \
    libproj-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip (important for wheel resolution)
RUN pip install --upgrade pip

# Copy requirements first (better caching)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . /app

EXPOSE 8001

CMD ["bash", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8001"]
