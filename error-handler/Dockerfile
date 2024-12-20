# Use Python 3.10 slim image as the base image
FROM python:3.10-slim

# Allow statements and log messages to immediately appear in the Cloud Run logs
ENV PYTHONUNBUFFERED=1

# Create a non-root user to avoid security risks
RUN adduser --no-create-home --disabled-password --gecos "" cruser
USER cruser
WORKDIR /home/cruser

# Copy the application dependency manifest and install dependencies
# This step is cached by Docker to avoid re-running pip install on every code change.
COPY --chown=cruser:cruser cont_intel/api/error-handler/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code and other necessary files
COPY --chown=cruser:cruser cont_intel/api/error-handler/src/ cont_intel/api/error-handler/src/
COPY --chown=cruser:cruser cont_intel/api/utils/ cont_intel/api/utils/

# Set PATH to include the user's local Python bin directory
ENV PATH="/home/cruser/.local/bin:${PATH}"

# Expose the port that Cloud Run will use (default 8080)
EXPOSE 8080

# Run the FastAPI application using Uvicorn
CMD ["uvicorn", "cont_intel.api.error-handler.src.api:app", "--host", "0.0.0.0", "--port", "8080"]
