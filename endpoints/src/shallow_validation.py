from fastapi import HTTPException
from typing import Union
from loguru import logger

import cont_intel.api.endpoints.src.schemas as schemas
from cont_intel.api.utils.api_utils import handle_error


def validate_request(request: Union[schemas.InferenceRequest, schemas.TrainRequest]):
    """
    Validates the given request to ensure required fields are correct.
    :param request: The request object (either InferenceRequest or TrainRequest)
    :raises HTTPException: If validation fails
    """
    try:
        validate_dataset(request)
    except HTTPException as e:
        logger.exception("Request validation failed")
        handle_error(request, e, 400)


def validate_dataset(request: Union[schemas.InferenceRequest, schemas.TrainRequest]):
    """
    Validates the dataset reference to ensure it is not None or empty.
    :param request: The request object (either InferenceRequest or TrainRequest)
    :raises HTTPException: If dataset reference is invalid
    """
    dataset = request.dataset_reference
    if not dataset or dataset.strip() == "":
        handle_error(request, Exception(f"Invalid dataset reference: '{dataset}' provided."), 400)
