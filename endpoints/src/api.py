from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from loguru import logger

from cont_intel.api.endpoints.src.routes import (
    AnnotationRoutes,
    InferenceRoutes,
    TrainingRoutes,
)
from cont_intel.api.utils.api_utils import handle_error

app = FastAPI()

# Include routers for different routes (inference, training, annotation)
@app.on_event("startup")
async def startup_event():
    """
    Event triggered on startup to configure routes.
    """
    try:
        app.include_router(InferenceRoutes().inference_routes, prefix="/inference", tags=["inference"])
        app.include_router(TrainingRoutes().training_routes, prefix="/training", tags=["training"])
        app.include_router(AnnotationRoutes().annotation_routes, prefix="/annotation", tags=["annotation"])
    except Exception as e:
        logger.exception("Error occurred during startup event")
        handle_error(None, e, 500)

@app.get("/", response_class=PlainTextResponse)
def read_root():
    """
    Root endpoint that returns a message indicating the API is up.
    """
    try:
        return "Content Intel MVP API"
    except Exception as e:
        logger.exception("Error occurred while processing the root request")
        handle_error(None, e, 204)
