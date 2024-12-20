from datetime import timedelta
from google.cloud import storage
from google.auth.transport import requests
from google import auth
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

app = FastAPI()

@app.post("/", response_class=PlainTextResponse)
async def generate_signed_url(request: Request):
    request_json = await request.json()

    # Ensure that required fields are in the request
    required_fields = ['bucket', 'objectname', 'timedelta']
    for field in required_fields:
        if field not in request_json:
            return PlainTextResponse(f"Missing required field: {field}", status_code=400)

    # Parse the timedelta field and generate the signed URL
    try:
        expiration_time = timedelta(days=int(request_json['timedelta']))
    except ValueError:
        return PlainTextResponse("Invalid timedelta value", status_code=400)

    return make_signed_url(request_json['bucket'], request_json['objectname'], exp=expiration_time)

def make_signed_url(bucket: str, objectname: str, *, exp: Optional[timedelta] = None) -> str:
    """
    Generate a signed URL for a Google Cloud Storage object, valid for the specified duration.
    
    Parameters:
    - bucket: Name of the GCS bucket.
    - objectname: Name of the object (file) within the bucket.
    - exp: Expiration time for the signed URL (default is 1 hour).
    
    Returns:
    - A signed URL as a string.
    """
    # Default expiration time
    if exp is None:
        exp = timedelta(hours=1)

    # Set the required Google Cloud Storage and IAM scopes
    SCOPES = [
        "https://www.googleapis.com/auth/devstorage.read_write",
        "https://www.googleapis.com/auth/iam"
    ]

    # Get the default credentials for the service account
    credentials, project_id = auth.default(scopes=SCOPES)

    # Refresh the credentials if the token is not available
    if credentials.token is None:
        credentials.refresh(requests.Request())

    # Initialize the Google Cloud Storage client with the credentials
    client = storage.Client(credentials=credentials)

    # Fetch the bucket and blob objects
    bucket_obj = client.get_bucket(bucket)
    blob = bucket_obj.blob(objectname)

    # Generate and return the signed URL
    return blob.generate_signed_url(
        version="v4",
        expiration=exp,
        service_account_email=credentials.service_account_email,
        access_token=credentials.token,
    )
