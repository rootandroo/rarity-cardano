from typing import Optional, List
from pydantic import BaseModel, Field
import uuid

class CollectionModel(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias='_id')
    name: str 
    tx_count: int = 0
    properties: List[str] = []
    policy_id: str
    facets: dict = {}   
    project: str

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "id": "0f0b4852-630d-455d-8c29-bb83fa7adcf9",
                "name": "Collection0000",
                "tx_count": 0,
                "properties": [],
                "policy_id": "7abad1ee1a3ca70010f9c61685c4",
                "facets": {},
                "project": "bd6b9931-c4c7-40d5-a2f7-0845b17fe316"
            }
        }


class UpdateCollectionModel(BaseModel):
    name: Optional[str]
    tx_count: Optional[int]
    properties: Optional[List[str]]
    policy_id: Optional[str]
    facets: Optional[dict]

    class Config:
        schema_extra = {
            "example": {
                "name": "Collection0000",
                "tx_count": 0,
                "properties": [],
                "policy_id": "7abad1ee1a3ca70010f9c61685c4",
                "facets": {}
            }
        }