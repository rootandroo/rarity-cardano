from typing import Optional
from pydantic import BaseModel, Field
import uuid

class ProjectModel(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias='_id')
    name: str

    class Config:   
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "id": "0f0b4852-630d-455d-8c29-bb83fa7adcf9",
                "name": "Project0000"
            }
        }

class UpdateProjectModel(BaseModel):
    name: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "name": "Project000"
            }
        }