# Use the slim version of Python to reduce size
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy only requirements first to leverage Docker cache
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . /app

# Expose the application port
EXPOSE 5000

# Compile translations
RUN pybabel compile -d app/translations

# Use Gunicorn for production, remove manage.py for simplicity
CMD ["gunicorn", "--worker-class", "gevent", "--timeout", "120", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]

