import json
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from loguru import logger

from cont_intel.api.utils.api_utils import publish_message, write_log, handle_error
from cont_intel.api.utils.data_classes import PubSubMessage
from cont_intel.reverse_image_search import reverse_image_search_main
from cont_intel.utils.gcp_utils import (
    download_file,
    save_to_bucket_from_string,
    store_annotation_info_to_bq,
)
from cont_intel.utils.secret_management import access_secret_version

app = FastAPI()

# Helper function to access secrets
def fetch_required_secrets():
    """Fetch necessary secrets for reverse image search."""
    try:
        return {
            "api_key": access_secret_version("GOOGLE_VISION_API_KEY"),
            "engine_id": access_secret_version("GOOGLE_VISION_ENGINE_ID"),
            "key_json": access_secret_version("GOOGLE_VISION_KEY_JSON"),
        }
    except Exception as e:
        logger.error(f"Error fetching secrets: {e}")
        raise RuntimeError("Failed to fetch required secrets")

# Helper function to prepare file paths
def prepare_file_paths(task_id: str, file_name: str = "image.png"):
    """Prepare necessary file paths for processing."""
    data_dir = Path(task_id)
    return data_dir, data_dir / file_name, data_dir / "key.json"

# Helper function to log and publish messages
def log_and_publish(pubsub_message_data: PubSubMessage, message: str, topic: str):
    """Log a message and publish it to Pub/Sub."""
    write_log("api", {"message": message, "request": pubsub_message_data.to_json()})
    publish_message(pubsub_message_data.project_id, topic, pubsub_message_data.to_json())

@app.post("/", response_class=PlainTextResponse)
async def read_root(request: Request):
    request_json = await request.json()

    try:
        # Log received request
        logger.info(f"Annotator received request: {request_json}")

        # Parse PubSub message
        pubsub_message_data = PubSubMessage.from_request(request_json)
        log_and_publish(pubsub_message_data, "Annotator started", "annotator_start")

        # Prepare file paths and download input file
        data_dir, image_path, key_json_path = prepare_file_paths(pubsub_message_data.task_id)
        download_file(pubsub_message_data.bucket_name, data_dir, image_path.name)

        # Fetch secrets and write key JSON to file
        secrets = fetch_required_secrets()
        key_json_path.write_text(secrets["key_json"])

        # Prepare arguments for reverse image search
        custom_args = (
            f"--input_image_file={image_path} "
            f"--google_api_key={secrets['api_key']} "
            f"--google_engine_id={secrets['engine_id']} "
            f"--key_json_file={key_json_path} "
        )

        # Perform reverse image search
        annotations = json.dumps(reverse_image_search_main.reverse_image_search(custom_args))
        pubsub_message_data.results = {"annotation": annotations}

        # Save annotations to bucket and store metadata in BigQuery
        save_to_bucket_from_string(
            bucket_name=pubsub_message_data.bucket_name,
            bucket_dir=data_dir,
            file_name="annotations.json",
            contents=annotations,
        )
        store_annotation_info_to_bq(
            bucket_name=pubsub_message_data.bucket_name,
            bucket_dir=pubsub_message_data.task_id,
            image_name=image_path.name,
            annotation_name="annotations.json",
            annotation_type=json.dumps(["reverse_image_search"]),
        )

        # Log success and publish completion message
        log_and_publish(pubsub_message_data, "Annotator ended", "annotator_end")
        return "Task processed successfully"

    except Exception as e:
        # Handle errors and return appropriate HTTP response
        handle_error(request_json, e, 500)
