# Use an official Python runtime as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app
COPY requirements.txt /app

# Copy the requirements.txt first for caching
#COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt


RUN apt-get update && apt-get install -y cron coreutils vim

# Copy the rest of your application code
COPY . /app

# Create a directory for logs
RUN mkdir -p /app/logs

# Expose port (optional, depending on the app)
EXPOSE 3000

# Command to run the backend application
CMD ["python", "app.py"]
