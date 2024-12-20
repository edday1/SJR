from datetime import timedelta
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from loguru import logger
from typing import Dict, Optional

import requests

from cont_intel.api.utils.api_utils import handle_error, write_log
from cont_intel.api.utils.data_classes import PubSubMessage
from cont_intel.utils.gcp_utils import make_signed_download_url

app = FastAPI()


@app.post("/", response_class=PlainTextResponse)
async def read_root(request: Request):
    request_json = await request.json()

    try:
        logger.info("Output received a request")

        pubsub_message_data = PubSubMessage.from_request(request_json)

        logger.info(f"PubSubMessage data extracted: {pubsub_message_data}")

        output_url = pubsub_message_data.output_url
        results = pubsub_message_data.results

        # Process inference or training results
        if "inference" in results:
            logger.info("Inference result set received")
            response_obj = await process_inference(results["inference"])

        elif "training" in results:
            logger.info("Training result set received")
            response_obj = await process_training(results["training"])

        else:
            logger.error("Error: unexpected output")
            write_log("api", {"message": "Error: unexpected output"})
            raise HTTPException(status_code=400, detail="Unexpected output")

        # Send the response to the output URL
        send_output(output_url, response_obj)

    except Exception as e:
        handle_error(request_json, e, 204)


async def process_inference(inference_results: Dict) -> Dict:
    bucket_name = inference_results["bucket_name"]
    signed_url_predictions = make_signed_download_url(
        bucket_name, inference_results["predictions"], exp=timedelta(hours=12)
    )

    signed_url_metrics = None
    if inference_results.get("metrics"):
        signed_url_metrics = make_signed_download_url(
            bucket_name, inference_results["metrics"], exp=timedelta(hours=12)
        )

    signed_url_explanations = None
    if inference_results.get("explanations"):
        signed_url_explanations = make_signed_download_url(
            bucket_name, inference_results["explanations"], exp=timedelta(hours=12)
        )

    response_obj = {
        "status": "success",
        "data": {
            "predictions": signed_url_predictions,
            "metrics": signed_url_metrics,
            "explanations": signed_url_explanations,
        },
    }

    logger.info(f"Inference response object: {response_obj}")
    return response_obj


async def process_training(training_results: Dict) -> Dict:
    bucket_name = training_results["bucket_name"]
    signed_url_explanations = None
    if training_results.get("explanations"):
        signed_url_explanations = make_signed_download_url(
            bucket_name, training_results["explanations"], exp=timedelta(hours=12)
        )

    response_obj = {
        "status": "success",
        "data": {
            "model_id": training_results["model_id"],
            "explanations": signed_url_explanations,
        },
    }

    logger.info(f"Training response object: {response_obj}")
    return response_obj


@app.post("/annotator_end", response_class=PlainTextResponse)
async def read_root_annotator_end(request: Request):
    request_json = await request.json()

    try:
        logger.info(f"Output received a request: {request_json}")

        pubsub_message_data = PubSubMessage.from_request(request_json)
        output_url = pubsub_message_data.output_url
        results = pubsub_message_data.results

        if "annotation" in results:
            response_obj = {
                "status": "success",
                "data": {"annotation": results["annotation"], "trace_id": pubsub_message_data.task_id},
            }
        else:
            logger.error("Error: unexpected output")
            write_log("api", {"message": "Error: unexpected output"})
            raise HTTPException(status_code=400, detail="Unexpected output")

        send_output(output_url, response_obj)
        return PlainTextResponse("Processed successfully", status_code=200)

    except Exception as e:
        handle_error(request_json, e, 204)


def send_output(output_url: str, response_obj: Dict):
    headers = {"content-type": "application/json"}
    write_log("api", {"message": f"Posting response: {response_obj}"})
    
    try:
        response = requests.post(output_url, headers=headers, json=response_obj)
        response.raise_for_status()  # Ensure HTTP errors are raised
        write_log("api", {"message": "Output sent successfully"})
    except requests.exceptions.RequestException as e:
         handle_error(request_json, e, 500)
