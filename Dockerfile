# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install system dependencies for audio processing (FFmpeg, libsndfile)
# Hugging Face Spaces require software to be built from apt
RUN apt-get update && apt-get install -y ffmpeg libsndfile1 git && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements and install them securely
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app's code
COPY . .

# Hugging face runs containers as a non-root user (user 1000)
# Make sure the static directory exists and is writable
RUN mkdir -p static && chmod 777 static

# Expose port 7860 (Hugging Face default)
EXPOSE 7860

# Run the app
CMD ["python", "app.py"]
