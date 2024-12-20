# Use a smaller base image with Python 3.10
FROM python:3.10-slim

# Ensure Python output is logged immediately in Cloud Run logs
ENV PYTHONUNBUFFERED=1

# Create a non-root user to avoid security risks
RUN adduser --no-create-home --disabled-password --gecos "" cruser
USER cruser
WORKDIR /home/cruser

# Copy application dependency manifests to the container image.
# This helps Docker cache the dependencies layer, avoiding unnecessary installations when code changes.
COPY --chown=cruser:cruser cont_intel/api/controller/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source files to the container
COPY --chown=cruser:cruser cont_intel/api/controller/src /home/cruser/cont_intel/api/controller/src/
COPY --chown=cruser:cruser cont_intel/api/utils /home/cruser/cont_intel/api/utils/
COPY --chown=cruser:cruser cont_intel/utils /home/cruser/cont_intel/utils/

# Set the local path for user-installed Python packages
ENV PATH="/home/cruser/.local/bin:${PATH}"

# Expose the port that the app will run on (default for Cloud Run is 8080)
EXPOSE 8080

# Command to run the FastAPI application using Uvicorn
CMD ["uvicorn", "cont_intel.api.controller.src.api:app", "--host", "0.0.0.0", "--port", "8080"]
