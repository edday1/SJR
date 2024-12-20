export PROJECT_ID=$(gcloud config list project --format "value(core.project)")

export GATEWAY_CONFIG_VERSION=3

gcloud api-gateway api-configs create api-config-v${GATEWAY_CONFIG_VERSION} \
 --api=api \
 --openapi-spec=api.yaml   \
--project=${PROJECT_ID} \
--backend-auth-service-account=api-gateway-sa@${PROJECT_ID}.iam.gserviceaccount.com
gcloud api-gateway gateways update api-gateway \
  --api=api --api-config=api-config-v${GATEWAY_CONFIG_VERSION} \
  --location=europe-west2 --project=${PROJECT_ID}