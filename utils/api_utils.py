import traceback
import urllib.request
from os import getenv
from typing import Dict

from google.cloud import logging, pubsub_v1, storage
from google.logging.type import log_severity_pb2 as severity
from loguru import logger

from cont_intel.api.utils.data_classes import PubSubMessage


def get_project():
    # todo: seems to be not very reliable. i.e. can return some weird id's like ua8b6d4381aa313ebp-tp in vertex
    try:
        # get the Google Cloud Project ID
        url = "http://metadata.google.internal/computeMetadata/v1/project/project-id"
        req = urllib.request.Request(url)
        req.add_header("Metadata-Flavor", "Google")
        project_id = urllib.request.urlopen(req).read().decode()
        if project_id not in [
            "x-contentintelligence-wpp-dev",
            "x-contentintelligence-wpp-tst",
            "x-contentintelligence-wpp-prod",
        ]:
            # todo: in some cases might be better to crash instead, rather than fail silently
            logger.error(f"Wrong google project id {project_id}, defaulting to 'x-contentintelligence-wpp-dev'")
            raise ValueError(f"Wrong project id {project_id}")
        return project_id
    except Exception as e:  # NOSONAR
        logger.info(f"Error while getting project_id: {str(e)}. Defaulting to 'x-contentintelligence-wpp-dev'")
        # in bitbucket the url can't be reached, so hardcode the project
        return "x-contentintelligence-wpp-dev"


def make_gcs_folder(project_id, task_id, bucket):
    gcs_client = storage.Client(project=project_id)
    bucket = gcs_client.get_bucket(bucket)
    blob = bucket.blob(task_id + "/")

    blob.upload_from_string("", content_type="application/x-www-form-urlencoded;charset=UTF-8")


def publish_message(project_id: str, topic_id: str, data_str: str) -> None:
    """Publishes message to a Pub/Sub topic."""

    publisher = pubsub_v1.PublisherClient()

    # The `topic_path` method creates a fully qualified identifier
    # in the form `projects/{project_id}/topics/{topic_id}`
    topic_path = publisher.topic_path(project_id, topic_id)

    # Data must be a bytestring
    data = "".join(data_str).encode("utf-8")

    # When you publish a message, the client returns a future.

    publisher.publish(topic_path, data)


def write_log(log_source: str, log_payload, log_severity: str = severity.INFO):
    client = logging.Client()
    logger = client.logger(log_source)

    if isinstance(log_payload, Dict):
        logger.log_struct(log_payload, severity=log_severity)
    else:
        logger.log_text(log_payload, severity=log_severity)


def handle_error(
    request: dict,
    e,
    error_code,
):
    try:
        SERVICE_NAME = getenv("K_SERVICE")
        logger.error(f"Service '{SERVICE_NAME}' failed: {e}")

        pubsub_message = PubSubMessage.from_request(request)
        logger.info(pubsub_message)

        error_message = f"Error in {SERVICE_NAME}. {''.join(traceback.format_exception_only(type(e), e)).strip()}"

        pubsub_message.error_message = error_message
        pubsub_message.error_code = error_code

        # Store the stack trace for internal debugging
        error_message += f", {traceback.format_exc()}"

        logger.info(f"Publish message to the pub/sub 'error' topic of the GCP project '{pubsub_message.project_id}'.")
        publish_message(pubsub_message.project_id, "error", pubsub_message.to_json())

        write_log("api", {"message": f"Error in {SERVICE_NAME}."})

    except Exception as e:
        write_log("api", {"message": "Error in handle_error routine!"})
        logger.error(f"handle_error routine failed: {e}")


def get_bucket_name(project_id):
    return dict(
        {
            "x-contentintelligence-wpp-dev": "api-input-dev",
            "x-contentintelligence-wpp-tst": "api-input-tst",
            "x-contentintelligence-wpp-prod": "api-input-prod",
        }
    ).get(project_id, "api-input-dev")


def get_vertex_bucket_name(project_id):
    return dict(
        {
            "x-contentintelligence-wpp-dev": "ci-vertex-dev",
            "x-contentintelligence-wpp-tst": "ci-vertex-tst",
            "x-contentintelligence-wpp-prod": "ci-vertex-prod",
        }
    ).get(project_id, "ci-vertex-dev")


def update_results_with_sampled_predictions(results, sample_size=10):
    # Use single line conditions with `and` for short-circuit evaluation
    if (
        isinstance(results, dict)
        and isinstance(results.get("inference"), dict)
        and isinstance(results["inference"].get("predictions"), list)
        and len(results["inference"]["predictions"]) >= sample_size
    ):
        # If all conditions pass, execute this block
        sampled_predictions = results["inference"]["predictions"][:sample_size]
        del results["inference"]["predictions"]  # Delete old predictions
        results["inference"].update({"sampled_predictions": sampled_predictions})  # Update results dictionary

    return results
