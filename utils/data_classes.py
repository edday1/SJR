from __future__ import annotations  # noqa

import base64
import json
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class TaskType(str, Enum):
    INFERENCE = "INFERENCE"
    TRAINING = "TRAINING"
    TRAINING_INFERENCE = "TRAINING_INFERENCE"
    INFERENCE_EXPLAINABILITY = "INFERENCE_EXPLAINABILITY"
    TRAINING_EXPLAINABILITY = "TRAINING_EXPLAINABILITY"
    ANNOTATION = "ANNOTATION"
    NONE = "NONE"


@dataclass
class PubSubMessage:
    """
    A class containing all the required data that is passed around between Cloud Run components by PubSub.
    """

    project_id: str
    task_id: str
    signed_file_url: str
    bucket_name: str
    task_type: str
    output_url: str
    input_data_type: str = "json"
    csv_data_config: Optional[dict] = None
    explainability: Optional[List[str]] = None
    dataset_reference: Optional[str] = None
    model_id: Optional[str] = None
    results: Optional[dict] = None
    error_message: Optional[str] = None
    error_code: Optional[int] = None

    @staticmethod
    def from_request(request_json: dict) -> PubSubMessage:
        pubsub_message_data = PubSubMessage.parse_pubsub_message_data(request_json)

        return PubSubMessage(
            project_id=pubsub_message_data["project_id"],
            task_id=pubsub_message_data["task_id"],
            signed_file_url=pubsub_message_data["signed_file_url"],
            dataset_reference=pubsub_message_data["dataset_reference"],
            bucket_name=pubsub_message_data["bucket_name"],
            task_type=pubsub_message_data["task_type"],
            output_url=pubsub_message_data["output_url"],
            model_id=pubsub_message_data["model_id"],
            input_data_type=pubsub_message_data["input_data_type"],
            csv_data_config=pubsub_message_data["csv_data_config"],
            explainability=pubsub_message_data["explainability"],
            results=pubsub_message_data["results"],
            error_message=pubsub_message_data.get("error_message", None),
            error_code=pubsub_message_data.get("error_code", None),
        )

    @staticmethod
    def parse_pubsub_message_data(request_json: dict):
        pubsub_message = request_json["message"]
        pubsub_message_data = base64.b64decode(pubsub_message["data"]).decode("utf-8").strip()
        return json.loads(pubsub_message_data)

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)
