# Use Python 3.10 Slim as a base image
FROM python:3.10-slim

# Ensure logs appear in Cloud Run without buffering
ENV PYTHONUNBUFFERED=1

# Create a non-root user for security
RUN adduser --disabled-password --gecos "" cruser

# Set user and working directory
USER cruser
WORKDIR /home/cruser

# Copy the requirements file and install dependencies
COPY --chown=cruser:cruser requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Ensure local user bin is included in PATH
ENV PATH="/home/cruser/.local/bin:${PATH}"

# Copy application files
COPY --chown=cruser:cruser signedurls.py src/

# Command to run the app using Uvicorn
CMD ["uvicorn", "src.signedurls:app", "--host", "0.0.0.0", "--port", "$PORT"]
