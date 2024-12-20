import pathlib
import requests
from google.cloud import storage
from loguru import logger

from cont_intel.api.utils.data_classes import TaskType
from cont_intel.api.utils.api_utils import handle_error


class DataTransferHandler:
    def __init__(self, bucket_name):
        self.gcs_client = storage.Client()
        # gcs
        self.bucket_gcs = self.gcs_client.get_bucket(bucket_name)

    def transfer_file_to_gcs(self, task_id: str, dataset_reference: str, signed_url: str, task_type: str, input_data_type: str):
        try:
            if task_type.lower() == TaskType.ANNOTATION.value.lower():
                file_name = "image.png"
                content_type = "image/png"
            else:
                file_name = f"data.{input_data_type}"  # "json" or "csv"
                content_type = "application/json"

            logger.info(f"Downloading file {file_name} from {signed_url}")
            # note: eventually this might need optimization to split into stream/chunks
            with requests.get(signed_url) as r:
                r.raise_for_status()
                logger.info("Downloading finished, proceeding to upload")
                return self._upload_file_to_gcs(r.text, task_id, dataset_reference, file_name, content_type)

        except requests.exceptions.RequestException as e:
            # Handle any issues with downloading the file
            logger.exception(f"Error occurred while downloading the file from {signed_url}")
            handle_error({'task_id': task_id, 'dataset_reference': dataset_reference, 'signed_url': signed_url}, e, 400)
        except Exception as e:
            # Catch other exceptions during file transfer
            handle_error({'task_id': task_id, 'dataset_reference': dataset_reference, 'signed_url': signed_url}, e, 500)

    def _upload_file_to_gcs(
        self, content: str, task_id: str, dataset_reference: str, file_name: str, content_type: str
    ):
        """
        Uploads the file to Google Cloud bucket
        """
        try:
            if dataset_reference:
                upload_path = str(pathlib.Path(task_id) / "input_data" / dataset_reference / file_name)
            else:
                upload_path = str(pathlib.Path(task_id) / "input_data" / file_name)

            logger.info(f"Uploading file {upload_path} to bucket {self.bucket_gcs}")
            blob = self.bucket_gcs.blob(upload_path)
            blob.upload_from_string(content, content_type=content_type)
            logger.info("File uploaded")
            return upload_path

        except Exception as e:
            # Handle errors during file upload to GCS
            handle_error({'task_id': task_id, 'dataset_reference': dataset_reference, 'file_name': file_name}, e, 500)
