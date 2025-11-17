# --- Fix 8: Dockerfile for Production Deployment ---
# Use the official Python slim base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project structure into the container
COPY . .

# Expose the port Streamlit runs on (default 8501)
EXPOSE 8501

# Set the entrypoint to run the Streamlit app
# Healthcheck enables Streamlit to run in production environments
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
