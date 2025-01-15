# Use the slim version of Python to reduce size
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the application port
EXPOSE 5000

# Compile translations
RUN pybabel compile -d app/translations

# Use Gunicorn for production with specified parameters
CMD ["gunicorn", "--worker-class", "eventlet", "--timeout", "120", "--keep-alive", "30", "-w", "4", "-b", "0.0.0.0:5000", "--access-logfile", "-", "--error-logfile", "-", "run:app"]
