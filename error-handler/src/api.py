import requests
from os import getenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from loguru import logger
from typing import Dict

from cont_intel.api.utils.api_utils import write_log
from cont_intel.api.utils.data_classes import PubSubMessage

app = FastAPI()

SERVICE_NAME = getenv("K_SERVICE")


@app.post("/", response_class=PlainTextResponse)
async def read_root(request: Request):
    try:
        # Parse the incoming JSON request
        request_json = await request.json()
        logger.info(f"{SERVICE_NAME} received a request: {request_json}")

        # Parse the PubSubMessage
        pubsub_message_data = PubSubMessage.from_request(request_json)

        output_url = pubsub_message_data.output_url
        error_message = pubsub_message_data.error_message

        # Construct response object
        response_obj = {"status": "Error", "data": {"Reason": error_message}}
        headers = {"Content-Type": "application/json"}

        # Log the response being posted
        write_log("api", {"message": f"Posting response to {output_url}", "response": response_obj})

        # Send the error response to the output URL
        try:
            response = requests.post(output_url, headers=headers, json=response_obj)
            response.raise_for_status()  # Raise an exception for HTTP errors
            write_log("api", {"message": "Error response posted successfully"})
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to post error response: {e}")
            write_log("api", {"message": f"Failed to post error response: {e}"})
            raise HTTPException(status_code=500, detail="Failed to send error response")

        write_log("api", {"message": "Error Handler completed successfully"})
        return PlainTextResponse("Error handler completed", status_code=200)

    except Exception as e:
        # Handle any other exceptions that occur during the process
        write_log("api", {"message": "Error in Error Handler!"})
        logger.error(f"Error Handler failed: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
