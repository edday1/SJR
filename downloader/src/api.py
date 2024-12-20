from os import getenv

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from loguru import logger

from cont_intel.api.downloader.src.utils.data_transfer_handler import DataTransferHandler
from cont_intel.api.utils.api_utils import get_bucket_name, get_project, handle_error, publish_message, write_log
from cont_intel.api.utils.data_classes import PubSubMessage

# Constants and initialization
app = FastAPI()
project_id = get_project()
bucket_name = get_bucket_name(project_id)
data_transfer_handler = DataTransferHandler(bucket_name)
SERVICE_NAME = getenv("K_SERVICE")


# Helper function to log and publish messages
def log_and_publish(pubsub_message_data: PubSubMessage, message: str, topic: str):
    """Log the message and publish to the specified Pub/Sub topic."""
    logger.info(message)
    write_log("api", {"message": message, "request": pubsub_message_data.to_json()})
    publish_message(pubsub_message_data.project_id, topic, pubsub_message_data.to_json())


@app.post("/", response_class=PlainTextResponse)
async def read_root(request: Request):
    request_json = await request.json()

    try:
        logger.info(f"{SERVICE_NAME} received a request: {request_json}")
        
        pubsub_message_data = PubSubMessage.from_request(request_json)
        logger.info(f"PubSubMessage created: {pubsub_message_data}")

        # Log the initial request and publish message to "downloader_start"
        write_log("api", {"message": f"{SERVICE_NAME} received a request", "request": pubsub_message_data.to_json()})
        log_and_publish(pubsub_message_data, "Downloader started", "downloader_start")

        # Extract necessary information from PubSub message
        task_id = pubsub_message_data.task_id
        dataset_reference = pubsub_message_data.dataset_reference
        signed_url = pubsub_message_data.signed_file_url

        # Start the file transfer process
        data_transfer_handler.transfer_file_to_gcs(
            task_id, dataset_reference, signed_url, pubsub_message_data.task_type, pubsub_message_data.input_data_type
        )

        # Log the completion of the download process and publish the "downloader_end" message
        write_log("api", {"message": "Downloader ended"})
        log_and_publish(pubsub_message_data, "Downloader ended", "downloader_end")
        
        return "200"

    except Exception as e:
        logger.exception(f"Error occurred while processing the request: {e}")
        handle_error(request_json, e, 204)
