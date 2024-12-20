from loguru import logger
import cont_intel.api.endpoints.src.schemas as schemas
from cont_intel.api.endpoints.src.shallow_validation import validate_request
from cont_intel.api.utils.api_utils import get_bucket_name, get_project, publish_message, write_log
from cont_intel.api.utils.data_classes import PubSubMessage, TaskType
from cont_intel.api.utils.api_utils import handle_error


class APIHandler:
    """
    Handler to execute internal API logic for initiating different types of tasks.
    """

    def __init__(self):
        try:
            self.project_id = get_project()
            self.bucket_name = get_bucket_name(self.project_id)
        except Exception as e:
            logger.exception("Error occurred during APIHandler initialization")
            handle_error(None, e, 500)
            

    def initiate_inference(self, request: schemas.InferenceRequest, task_id: str):
        """
        Initiates inference request and sends it to the controller.
        """
        try:
            validate_request(request)
            task_type = self._get_task_type(request.explainability, TaskType.INFERENCE, TaskType.INFERENCE_EXPLAINABILITY)
            
            controller_request = self._create_pubsub_message(
                task_id=task_id,
                task_type=task_type,
                request=request
            )
            
            logger.info(f"Initiating inference with request: {controller_request}")
            self._create_pubsub_for_controller(controller_request)
        except Exception as e:
            logger.exception("Error occurred while initiating inference")
            handle_error(request, e, 500)
            

    def initiate_training(self, request: schemas.TrainRequest, task_id: str):
        """
        Initiates training request and sends it to the controller.
        """
        try:
            validate_request(request)
            task_type = self._get_task_type(request.explainability, TaskType.TRAINING, TaskType.TRAINING_EXPLAINABILITY)

            controller_request = self._create_pubsub_message(
                task_id=task_id,
                task_type=task_type,
                request=request
            )

            logger.info(f"Initiating training with request: {controller_request}")
            self._create_pubsub_for_controller(controller_request)
        except Exception as e:
            logger.exception("Error occurred while initiating training")
            handle_error(request, e, 500)
            

    def initiate_annotation(self, request: schemas.AnnotationRequest, task_id: str):
        """
        Initiates annotation request and sends it to the controller.
        """
        try:
            controller_request = PubSubMessage(
                task_id=task_id,
                project_id=self.project_id,
                task_type=str(TaskType.ANNOTATION.value),
                signed_file_url=request.signed_file_url,
                output_url=request.output_url,
                model_id=None,
                dataset_reference=None,
                bucket_name=self.bucket_name,
            )

            logger.info(f"Initiating annotation with request: {controller_request}")
            self._create_pubsub_for_controller(controller_request)
        except Exception as e:
            logger.exception("Error occurred while initiating annotation")
            handle_error(request, e, 500)

    def _get_task_type(self, explainability: list, default_task_type: TaskType, explainability_task_type: TaskType) -> str:
        """
        Determines the appropriate task type based on whether explainability is enabled.
        """
        try:
            return str(explainability_task_type if len(explainability) > 0 else default_task_type)
        except Exception as e:
            logger.exception("Error occurred while determining task type")
            handle_error(None, e, 500)

    def _create_pubsub_message(self, task_id: str, task_type: str, request: schemas.InferenceRequest | schemas.TrainRequest) -> PubSubMessage:
        """
        Creates a PubSubMessage from the provided request details.
        """
        try:
            return PubSubMessage(
                task_id=task_id,
                project_id=self.project_id,
                task_type=task_type,
                signed_file_url=request.signed_file_url,
                output_url=request.output_url,
                model_id=request.model_id if hasattr(request, 'model_id') else None,
                dataset_reference=request.dataset_reference if hasattr(request, 'dataset_reference') else None,
                bucket_name=self.bucket_name,
                input_data_type=request.input_data_type,
                csv_data_config=request.csv_data_config if hasattr(request, 'csv_data_config') else None,
                explainability=request.explainability if hasattr(request, 'explainability') else None,
            )
        except Exception as e:
            logger.exception("Error occurred while creating PubSub message")
            handle_error(None, e, 500)

    def _create_pubsub_for_controller(self, pubsub_request: PubSubMessage):
        """
        Creates a PubSub message for the controller and publishes it.
        """
        try:
            json_payload = {
                "message": "API request in Endpoints, start Controller",
                "pipe_request": pubsub_request.to_json(),
            }
            write_log("api", json_payload)
            publish_message(pubsub_request.project_id, "controller_start", pubsub_request.to_json())
            logger.info(f"PubSub message sent to controller: {pubsub_request}")
        except Exception as e:
            logger.error(f"Error while publishing message to controller: {e}")
            handle_error(None, e, 500)
