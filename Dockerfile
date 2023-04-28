# Use an official Python runtime as a parent image
FROM python:latest

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . .

# Expose port 80 for the bot to listen on
EXPOSE 80

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    TZ=UTC

# Run the bot on container startup
CMD ["python", "techBot.py"]
