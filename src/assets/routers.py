import json
from fastapi import APIRouter, Body, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pymongo import UpdateOne
from typing import List

from .models import AssetModel, UpdateAssetModel
from routers import get_router

def get_assets_router(app):
    app.include_router(get_router(app, AssetModel, UpdateAssetModel, 'asset'))
    assets_router = APIRouter(
        prefix='/asset',
        tags=['assets']
    )

    @assets_router.get("/policy/{id}", response_model=List[AssetModel], response_description="List assets by collection")
    async def list_by_policy_id(id: str, request: Request):
        assets = []
        for doc in await request.app.db['assets'].find({'collection': id}).to_list(length=None):
            assets.append(doc)
        return assets
    
    @assets_router.post("/bulk/", response_model=AssetModel, response_description="Bulk insert assets")
    async def bulk_create(request: Request, assets: List[AssetModel] = Body(...)):
        assets = jsonable_encoder(assets)

        new_assets = await request.app.db['assets'].insert_many(assets)
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED, content=f'Created {len(new_assets.inserted_ids)} assets'
        )
    
    @assets_router.put("/bulk/", response_model=AssetModel, response_description="Bulk update assets")
    async def bulk_update(request: Request, assets: List[UpdateAssetModel] = Body(...)):
        assets = jsonable_encoder(assets)
        operations = []
        for asset in assets:
            filter = {"name": asset['name'], "collection": asset['collection']}
            update = {"$set": { "rarity": asset['rarity'], "metadata": asset['metadata'] }}
            operations.append(UpdateOne(filter, update))

        updated_assets = await request.app.db['assets'].bulk_write(operations)
        return JSONResponse(content=f'Updated {updated_assets.modified_count} assets')
    return assets_router