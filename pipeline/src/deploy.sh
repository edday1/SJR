export PROJECT_ID=$(gcloud config list project --format "value(core.project)")
export IMAGE_NAME=pipeline
export IMAGE_URI=europe-west2-docker.pkg.dev/${PROJECT_ID}/cont-intel-api/${IMAGE_NAME}
docker build -f cont_intel/api/${IMAGE_NAME}/Dockerfile -t ${IMAGE_URI} ./
docker push ${IMAGE_URI}
gcloud builds submit --config '/home/ed/OneDrive/job/satalia/x_innovations_contentpredictionpoc_wpp/cont_intel/api/pipeline/cloudbuild _deploy_only.yaml'