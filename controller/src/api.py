from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from loguru import logger

from cont_intel.api.utils.api_utils import handle_error, publish_message, write_log
from cont_intel.api.utils.data_classes import PubSubMessage, TaskType

app = FastAPI()

# Helper function to log and publish messages in a more centralized manner
def log_and_publish(pubsub_message_data: PubSubMessage, message: str, topic: str):
    """Log the message and publish to the specified Pub/Sub topic."""
    logger.info(message)
    write_log("api", {"message": message, "request": pubsub_message_data.to_json()})
    publish_message(pubsub_message_data.project_id, topic, pubsub_message_data.to_json())

@app.post("/", response_class=PlainTextResponse)
async def read_root(request: Request):
    request_json = await request.json()

    try:
        logger.info(f"Controller received a request: {request_json}")
        
        pubsub_message_data = PubSubMessage.from_request(request_json)
        logger.info(f"PubSubMessage created: {pubsub_message_data}")

        # Log the initial request and publish message to "downloader_start"
        log_and_publish(pubsub_message_data, "Triggering downloader", "downloader_start")
        return "Request successfully received and processed"

    except Exception as e:
        # Handle any error that occurs during the request processing
        logger.exception("Error occurred while processing the request")
        handle_error(request_json, e, 204)
        raise HTTPException(status_code=204, detail="Error processing the request")

@app.post("/downloader_end", response_class=PlainTextResponse)
async def read_downloader_end(request: Request):
    request_json = await request.json()

    try:
        pubsub_message_data = PubSubMessage.from_request(request_json)
        logger.info(f"PubSubMessage created: {pubsub_message_data}")

        # Process based on task type and proceed with the next pipeline step
        if pubsub_message_data.task_type in [
            TaskType.TRAINING.value,
            TaskType.INFERENCE.value,
            TaskType.INFERENCE_EXPLAINABILITY.value,
            TaskType.TRAINING_EXPLAINABILITY.value,
        ]:
            log_and_publish(pubsub_message_data, "Data download ended, continuing pipeline", "pipeline_start")
        
        elif pubsub_message_data.task_type == TaskType.ANNOTATION.value:
            log_and_publish(pubsub_message_data, "Data download ended, starting annotation", "annotator_start")
        
        return "Data download process completed successfully"

    except Exception as e:
        logger.exception("Error occurred in downloader_end processing")
        handle_error(request_json, e, 204)
        raise HTTPException(status_code=204, detail="Error processing downloader_end request")
