FROM python:3.10-slim-bullseye

# Allow statements and log messages to immediately appear in the Cloud Run logs
ENV PYTHONUNBUFFERED=1

# Add custom alibi library
COPY alibi/ alibi/.

# Use less deps for actual pipeline runs - remove dev packages
COPY requirements-pipeline.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Install necessary system libraries and dependencies in one layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    unzip \
    firefox-esr && \
    rm -rf /var/lib/apt/lists/*  # Clean up to reduce image size

# Install gecko driver (download only once)
RUN curl -L --proto "=https" https://github.com/mozilla/geckodriver/releases/download/v0.30.0/geckodriver-v0.30.0-linux64.tar.gz | \
    tar xz -C /usr/local/bin

# Download NLTK data
RUN python3 -c "import nltk; nltk.download('punkt', download_dir='/usr/local/nltk_data');  nltk.download('stopwords', download_dir='/usr/local/nltk_data')"

# Download pretrained transformers model
RUN mkdir -p /tmp/hugging-face-models/paraphrase-multilingual-mpnet-base-v2 && \
    cd /tmp/hugging-face-models/paraphrase-multilingual-mpnet-base-v2 && \
    curl -sS https://public.ukp.informatik.tu-darmstadt.de/reimers/sentence-transformers/v0.2/paraphrase-multilingual-mpnet-base-v2.zip -o model.zip && \
    unzip model.zip && \
    rm model.zip

# Copy application code and cont_intel code with correct ownership in a single command
COPY --chown=cruser:cruser app/ app/
COPY --chown=cruser:cruser cont_intel/ cont_intel/
COPY --chown=cruser:cruser config/ config/

# Install additional required Python packages
RUN pip3 install --no-cache-dir -r cont_intel/api/pipeline/requirements.txt

# Create a non-root user and avoid security risks
RUN adduser --no-create-home --disabled-password --gecos "" cruser

# Change ownership of necessary files
RUN chown -R cruser:cruser /tmp/hugging-face-models /config

# Switch to the non-root user
USER cruser

# Set Python path
ENV PYTHONPATH="${PYTHONPATH}:/app:/"

# Expose the port that Cloud Run will use (default 8080)
EXPOSE 8080

# Run the FastAPI application using Uvicorn
CMD ["uvicorn", "cont_intel.api.pipeline.src.api:app", "--host", "0.0.0.0", "--port", "8080"]
