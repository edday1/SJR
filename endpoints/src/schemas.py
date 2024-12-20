from typing import List, Optional, Dict

from pydantic import BaseModel, constr, Field


class AnnotationRequest(BaseModel):
    signed_file_url: constr(regex=r"^https?://[^\s/$.?#].[^\s]*$")  # Ensure the URL is valid
    output_url: constr(regex=r"^https?://[^\s/$.?#].[^\s]*$")  # Ensure the URL is valid

    class Config:
        orm_mode = True
        min_anystr_length = 1  # Ensure all string fields are non-empty


class InferenceRequest(BaseModel):
    signed_file_url: constr(regex=r"^https?://[^\s/$.?#].[^\s]*$")  # Ensure the URL is valid
    output_url: constr(regex=r"^https?://[^\s/$.?#].[^\s]*$")  # Ensure the URL is valid
    dataset_reference: str = "used_dataset"
    model_id: str
    input_data_type: str = "json"
    csv_data_config: Optional[Dict] = None  # Optional config for CSV
    explainability: List[str] = Field(default_factory=list, description="List of explainability methods")

    class Config:
        orm_mode = True
        min_anystr_length = 1  # Ensure all string fields are non-empty
        anystr_strip_whitespace = True  # Strip whitespaces in string fields


class TrainRequest(BaseModel):
    signed_file_url: constr(regex=r"^https?://[^\s/$.?#].[^\s]*$")  # Ensure the URL is valid
    output_url: constr(regex=r"^https?://[^\s/$.?#].[^\s]*$")  # Ensure the URL is valid
    dataset_reference: str = "used_dataset"
    source_model_id: Optional[str] = None
    input_data_type: str = "json"
    csv_data_config: Optional[Dict] = None  # Optional config for CSV
    explainability: List[str] = Field(default_factory=list, description="List of explainability methods")

    class Config:
        orm_mode = True
        min_anystr_length = 1  # Ensure all string fields are non-empty
        anystr_strip_whitespace = True  # Strip whitespaces in string fields
