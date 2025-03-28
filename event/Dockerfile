# Use a minimal and efficient Python image
FROM python:3.12-alpine

# Set the working directory
WORKDIR /app

# Install system dependencies for building Python packages (Alpine requires these)
# RUN apk add --no-cache gcc musl-dev libffi-dev

# Copy only the requirements file first (to leverage Docker's caching mechanism)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the FastAPI default port
EXPOSE 8001

# Run the FastAPI application with Uvicorn
CMD ["uvicorn", "event_service:app", "--host", "0.0.0.0", "--port", "8001"]
