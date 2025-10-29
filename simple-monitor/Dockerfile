FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application and environment
COPY telegram_monitor.py .
COPY setup_session.py .
COPY .env .
COPY telegram_monitor.session .

# Create logs directory
RUN mkdir -p logs

# Expose the health check port
EXPOSE 8000

# Run the monitor
CMD ["python", "telegram_monitor.py"]