# Use a smaller base image with Python 3.10
FROM python:3.10-slim

# Ensure Python output is logged immediately in Cloud Run logs
ENV PYTHONUNBUFFERED=1

# Set working directory for the application inside the container
WORKDIR /app

# Copy application dependency manifests to the container image.
# This step helps in leveraging Docker cache to avoid reinstalling dependencies unless requirements.txt changes.
COPY cont_intel/api/annotator/requirements.txt ./requirements.txt

# Install dependencies listed in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source files to the container
COPY cont_intel/api/annotator/src /app/cont_intel/api/annotator/src/
COPY cont_intel/api/utils /app/cont_intel/api/utils/
COPY cont_intel/utils /app/cont_intel/utils/
COPY cont_intel/reverse_image_search /app/cont_intel/reverse_image_search/

# Install OpenCV and other required system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*  # Clean up to reduce image size

# Ensure NLTK dependencies are installed for text processing
RUN python3 -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Expose the port the app will run on (usually 8080 for Cloud Run)
EXPOSE 8080

# Command to run the FastAPI application using Uvicorn
CMD ["uvicorn", "cont_intel.api.annotator.src.api:app", "--host", "0.0.0.0", "--port", "8080"]
