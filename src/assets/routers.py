from fastapi import APIRouter, Body, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import List

from .models import AssetModel


def get_assets_router(app):
    assets_router = APIRouter(
        prefix='/assets',
        tags=['assets']
    )

    @assets_router.get("/collection/{id}", response_model=List[AssetModel], response_description="List assets by collection")
    async def list_by_collection_id(id: str, request: Request):
        assets = []
        for doc in await request.app.db['assets'].find({'collection': id}).to_list(length=None):
            assets.append(doc)
        return assets
    
    return assets_router