FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY backend/ .

# Expose the port the app runs on
EXPOSE 5000

# Use the virtual environment's Python executable to run the app
CMD ["python", "app.py"]