import uuid
from fastapi import APIRouter, status
from loguru import logger

import cont_intel.api.endpoints.src.schemas as schemas
from cont_intel.api.endpoints.src.api_handler import APIHandler
from cont_intel.api.utils.api_utils import handle_error


class InferenceRoutes:
    """
    Inference-specific routes for initiating an inference task.
    """
    def __init__(self, api_handler: APIHandler):
        self.inference_routes = APIRouter()
        self.api_handler = api_handler
        self._init_routes()

    def _init_routes(self):
        """
        Initializes the POST route for initiating an inference task.
        """
        @self.inference_routes.post(
            "/initiate", status_code=status.HTTP_201_CREATED, response_model=schemas.InferenceRequest
        )
        async def initiate_inference(request: schemas.InferenceRequest) -> schemas.InferenceRequest:
            task_id = uuid.uuid4().hex
            try:
                self.api_handler.initiate_inference(request, task_id)
                return request
            except Exception as e:
                logger.exception("Error occurred while initiating inference")
                handle_error(request, e, 500)


class TrainingRoutes:
    """
    Training-specific routes for initiating a training task.
    """
    def __init__(self, api_handler: APIHandler):
        self.training_routes = APIRouter()
        self.api_handler = api_handler
        self._init_routes()

    def _init_routes(self):
        """
        Initializes the POST route for initiating a training task.
        """
        @self.training_routes.post(
            "/initiate", status_code=status.HTTP_201_CREATED, response_model=schemas.TrainRequest
        )
        async def initiate_training(request: schemas.TrainRequest) -> schemas.TrainRequest:
            task_id = uuid.uuid4().hex
            try:
                self.api_handler.initiate_training(request, task_id)
                return request
            except Exception as e:
                logger.exception("Error occurred while initiating training")
                handle_error(request, e, 500)


class AnnotationRoutes:
    """
    Annotation-specific routes for initiating an annotation task.
    """
    def __init__(self, api_handler: APIHandler):
        self.annotation_routes = APIRouter()
        self.api_handler = api_handler
        self._init_routes()

    def _init_routes(self):
        """
        Initializes the POST route for initiating an annotation task.
        """
        @self.annotation_routes.post(
            "/initiate", status_code=status.HTTP_201_CREATED, response_model=schemas.AnnotationRequest
        )
        async def initiate_annotation(request: schemas.AnnotationRequest) -> schemas.AnnotationRequest:
            task_id = uuid.uuid4().hex
            try:
                self.api_handler.initiate_annotation(request, task_id)
                return request
            except Exception as e:
                logger.exception("Error occurred while initiating annotation")
                handle_error(request, e, 500)
