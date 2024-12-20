import json
import os
from typing import Dict, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from loguru import logger

from cont_intel.api.utils.api_utils import (
    handle_error,
    publish_message,
    update_results_with_sampled_predictions,
    write_log,
)
from cont_intel.api.utils.data_classes import PubSubMessage
from cont_intel.api.vertex.vertex_pred import get_job
from cont_intel.utils.gcp_utils import message_id_stored_in_bq, store_message_id_to_bq
from cont_intel.wrapper import main_new as wrapper_main_new

app = FastAPI()

def extract_custom_args_from_pub_sub_message(pubsub_message_data: PubSubMessage) -> str:
    """
    Constructs a string of custom arguments for the pipeline based on the PubSub message.
    """
    bucket_name = pubsub_message_data.bucket_name
    task_id = pubsub_message_data.task_id
    model_id = pubsub_message_data.model_id
    task_name = pubsub_message_data.task_type
    dataset_reference = pubsub_message_data.dataset_reference
    explainability = pubsub_message_data.explainability
    input_data_type = pubsub_message_data.input_data_type
    csv_data_config = pubsub_message_data.csv_data_config

    custom_args = (
        f"--bucket_name={bucket_name} "
        f"--bucket_dir={task_id} "
        f"--task_name={task_name} "
        f"--dataset_name={dataset_reference} "
        f"--input_data_type={input_data_type} "
    )

    if model_id:
        custom_args += f" --model_id={model_id} "

    if input_data_type == "csv":
        custom_args += f"--csv_data_config={csv_data_config} "

    if explainability:
        custom_args += f"--explainability={' '.join(explainability)} "

    return custom_args


def msg_already_processed(request_json: dict, project_id: str) -> bool:
    """
    Checks if the message has already been processed based on the message_id.
    """
    try:
        message_id = int(request_json["message"]["message_id"])
        logger.info(f"Checking whether the message {message_id} has already been processed...")
        
        already_processed = message_id_stored_in_bq(message_id, project_id=project_id)
        if already_processed:
            logger.warning(f"Skipping message {message_id} as it was already processed.")
            return True

        store_message_id_to_bq(message_id, project_id=project_id)
        return False
    except Exception as e:
        logger.error(f"Error checking message processing status: {e}")
        logger.warning("Proceeding to process the message without the checks.")
        return False


@app.post("/", response_class=PlainTextResponse)
async def read_root(request: Request):
    request_json = await request.json()

    try:
        logger.info(f"Pipeline received a request: {request_json}")
        pubsub_message_data = PubSubMessage.from_request(request_json)
        logger.info(f"PubSubMessage created: {pubsub_message_data}")

        if msg_already_processed(request_json, project_id=pubsub_message_data.project_id):
            return "200"

        logger.info("Message is new - continuing to process")
        write_log("api", {"message": "Pipeline started", "pipe_request": pubsub_message_data.to_json()})

        # Start main pipeline process
        custom_args = extract_custom_args_from_pub_sub_message(pubsub_message_data)
        use_vertex = os.getenv("USE_VERTEX", "false").lower() == "true"
        
        if use_vertex:
            logger.info("Running pipeline using Vertex AI")
            pipeline_job = get_job(custom_args, project_id=pubsub_message_data.project_id)
            pipeline_job.submit()
            pipeline_job.wait()
            task_details = pipeline_job.to_dict().get("jobDetail", {}).get("taskDetails", [])
            pipeline_results = next(
                (task["execution"]["metadata"]["output:Output"] for task in task_details if "output:Output" in task["execution"]["metadata"]),
                None
            )
            if pipeline_results is None:
                raise ValueError("No pipeline results found.")
            results = json.loads(pipeline_results)
        else:
            logger.info("Running pipeline using Cloud Run")
            results = wrapper_main_new.main(custom_args, project_id=pubsub_message_data.project_id)

        # Update results with sampled predictions and log results
        pubsub_message_data.results = update_results_with_sampled_predictions(results)
        write_log("api", {"message": "Pipeline ended", "pipe_request": pubsub_message_data.to_json()})

        logger.info("Publishing message indicating pipeline completion")
        publish_message(pubsub_message_data.project_id, "pipeline_end", pubsub_message_data.to_json())

        return PlainTextResponse("Pipeline completed successfully", status_code=200)

    except Exception as e:
        logger.error(f"Error processing pipeline request: {e}")
        handle_error(request_json, e, 204)
        raise HTTPException(status_code=500, detail="Internal Server Error")

