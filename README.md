# API

The system described in the diagram is an **Annotation API** that facilitates an automated process for annotating images. The system is designed to automate the flow of image annotation, from receiving the initial request, downloading and storing the image, running the annotation job, and finally returning the results. It uses cloud-based storage (GCS) for managing image data and annotations and relies on event-driven communication ( through **PubSub**) to coordinate tasks across different components. Each component is a service running on GCP Cloud Run.
 Here's a breakdown of the system's flow (there is a diagram, **docs/api.png**, which illustrates this):

### Key Components:
1. **Hogarth**: A client making an initial annotation request.
2. **Gateway**: Serves as a middleware or API gateway that routes requests to the appropriate endpoints.
3. **Endpoints**: Represents the service endpoints for handling requests.
4. **Controller**: Manages the coordination of tasks and triggers the image processing pipeline.
5. **Downloader**: A service that downloads the image from a specified location.
6. **Annotator**: A service that performs the annotation of the image.
8. **Output**: The final component that constructs and sends the result of the annotation back to the requesting service.

### System Flow:
1. **Initial Request**:
    - **Hogarth** sends an `annotation_request` to the **Gateway**.
    - The **Gateway** forwards this request to the appropriate **Endpoints**, which acknowledges the request with a 201 status (success).
    - The **Gateway** then sends a success response back to **Hogarth**.

2. **Annotation Initialization**:
    - The **Endpoints** trigger the **Controller** to start the annotation process (via `annotator_start`).
    - A message is published via **PubSub**.
    - The **Controller** then signals the **Downloader** to begin downloading the image (`downloader_start`), using **PubSub** for communication.
    - The **Downloader** requests the image from **Hogarth**, which responds with the downloaded image. The image is then stored in **GCS**.

3. **Image Annotation**:
    - Once the image is stored, the **Downloader** signals the **Controller** that the image is ready (`downloader_end`), again via **PubSub**.
    - The **Controller** then signals the **Annotator** to begin the annotation process (`Annotator_start`), with **PubSub** ensuring communication.
    - The **Annotator** retrieves the image from **GCS** for processing.
    - After processing, the **Annotator** stores the annotations back in **GCS** and signals the end of the process (`Annotator_end`).

4. **Final Output**:
    - The **Output** component constructs the final response based on the annotations and other results.
    - The URL of the completed annotation results is sent back to **Hogarth** through a POST request.


## Although there is some code missing for non disclosure reasons, there are the details for creating the API:

Before running the commands make sure you are in the correct project. use ```gcloud config list``` to see. For example,
if you want to run these commands to `-prod` environment, run `gcloud config set project x-contentintelligence-wpp-prod`
before.

## Infrastructure using gcloud

The following commands were used to build the project's infrastructure:

- Set up PROJECT_ID and SERVICE_NAME:

```
export PROJECT_ID=$(gcloud config list project --format "value(core.project)")
export SERVICE_NAME=<name of the component you want to set permissions to. Usually name is equivalent of python module name. e.g. downloader>
export INPUT_TOPIC=<name of input topic you want the service to read. e.g. downloader_start>
export OUTPUT_TOPIC=<name of output topic you want the service to read. e.g. downloader_end>
```

### Before deployment

- Create service account:

```bash
gcloud iam service-accounts create ${SERVICE_NAME}-sa
``` 

- Add required roles (write to logs, publish pubsub messages etc.):

```bash
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
--member serviceAccount:${SERVICE_NAME}-sa@${PROJECT_ID}.iam.gserviceaccount.com \
--role=roles/logging.logWriter

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
--member serviceAccount:${SERVICE_NAME}-sa@${PROJECT_ID}.iam.gserviceaccount.com \
--role=roles/storage.admin 
```

- For bigquery access

```bash
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
--member serviceAccount:${SERVICE_NAME}-sa@${PROJECT_ID}.iam.gserviceaccount.com \
--role=roles/bigquery.dataEditor
```

OPTIONAL: you can check whether the roles have been added using this:

```bash
gcloud projects get-iam-policy ${PROJECT_ID} \
--flatten="bindings[].members" \
--format='table(bindings.role)' \
--filter="bindings.members:${SERVICE_NAME}-sa@${PROJECT_ID}.iam.gserviceaccount.com"
```

- Add roles to service in order to allow Cloud Build account to be able to deploy

IMPORTANT NOTE: At this point, please run the `gcloud builds submit --config <path to your yaml file>` to deploy the
service, since this command can be run only after the service has been deployed.

IMPORTANT NOTE: Cloud Build service accounts are different in different environments! For this one you might need to go
to IAM and find the right Cloud Build service account.
For prod it's `xxx@cloudbuild.gserviceaccount.com`, for dev it's `yyy@cloudbuild.gserviceaccount.com`

```bash
gcloud run services add-iam-policy-binding ${SERVICE_NAME} \
--member=serviceAccount:97831426579@cloudbuild.gserviceaccount.com \
--role=roles/run.developer \
--region=europe-west2
```

```bash
gcloud iam service-accounts add-iam-policy-binding ${SERVICE_NAME}-sa@${PROJECT_ID}.iam.gserviceaccount.com \
--member=serviceAccount:97831426579@cloudbuild.gserviceaccount.com \
--role=roles/iam.serviceAccountUser 
```

- Create pub/sub topics - relevant iff this component interacts with pubsub topics and they are not yet defined

```bash
gcloud pubsub topics create ${INPUT_TOPIC}
gcloud pubsub topics create ${OUTPUT_TOPIC}
```

- Create pub/sub subscriptions - relevant iff this component interacts with pubsub topics
    - Note: this step must be performed AFTER having deployed the CR because it needs to reference the CR endpoints
    - Also note that this step requires some manual adjustments depending on your flow. Different components might read
      different topics.

```bash
gcloud pubsub subscriptions create sub_${INPUT_TOPIC} --topic ${INPUT_TOPIC} \
--ack-deadline=600 \
--push-endpoint=https://${SERVICE_NAME}-<insert your tag here>-nw.a.run.app \
--push-auth-service-account=cloud-run-pubsub-invoker@${PROJECT_ID}.iam.gserviceaccount.com \
--push-auth-token-audience=https://${SERVICE_NAME}-<insert your tag here>-nw.a.run.app
```

```bash
gcloud pubsub subscriptions create sub_${OUTPUT_TOPIC} --topic ${OUTPUT_TOPIC} \
--ack-deadline=600 \
--push-endpoint=https://${SERVICE_NAME}-<insert your tag here>-nw.a.run.app \
--push-auth-service-account=cloud-run-pubsub-invoker@${PROJECT_ID}.iam.gserviceaccount.com \
--push-auth-token-audience=https://${SERVICE_NAME}-<insert your tag here>-nw.a.run.app
```
