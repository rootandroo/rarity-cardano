from typing import Optional
from pydantic import BaseModel, Field
import uuid


class AssetModel(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias='_id')
    name: str
    rarity: Optional[int] = 0
    metadata: dict 
    collection: str

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "name":"Asset0000",
                "metadata": {},
                "collection": "7abad1ee1a3ca70010f9c61685c4"
            }
        }

class UpdateAssetModel(BaseModel):
    name: Optional[str]
    rarity: Optional[int]
    metadata: Optional[dict]
    collection: str
    
    class Config:
        schema_extra = {
            "example": {
                "id": "0f0b4852-630d-455d-8c29-bb83fa7adcf9",
                "name":"Asset0000",
                "rarity": 0,
                "metadata": {}
            }
        }