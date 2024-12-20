export PROJECT_ID=$(gcloud config list project --format "value(core.project)")

export IMAGE_URI=europe-west2-docker.pkg.dev/${PROJECT_ID}/cont-intel-api/endpoints

gcloud builds submit  -t ${IMAGE_URI}

gcloud run deploy endpoints \
--image ${IMAGE_URI}  \
--service-account endpoints-sa \
--region="europe-west2" \
--no-allow-unauthenticated \
--ingress=internal 
# --tag 'run-endpoints'