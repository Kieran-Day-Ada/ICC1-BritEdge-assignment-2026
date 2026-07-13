FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Install system dependencies (libpq-dev/gcc are needed to build psycopg2)
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files
COPY . .

# Expose port (matches the default PORT used by application.py)
EXPOSE 8080

# Production WSGI server - the same startup command used on Azure App Service,
# so a working Docker container is a good local test of your App Service config.
CMD ["gunicorn", "--bind=0.0.0.0:8080", "--timeout", "600", "application:app"]
