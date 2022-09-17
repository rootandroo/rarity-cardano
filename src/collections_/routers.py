from fastapi import APIRouter, Body, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import List

from .models import CollectionModel, UpdateCollectionModel
from routers import get_router

def get_collections_router(app):
    app.include_router(get_router(app, CollectionModel, UpdateCollectionModel, 'collection'))

    collections_router = APIRouter(
        prefix='/collection',
        tags=['collections']
    )

    @collections_router.get("/project/{id}", response_model=List[CollectionModel], response_description="List collections by project")
    async def list_by_project_id(id: str, request: Request):
        collections = []
        for doc in await request.app.db['collections'].find({'project': id}).to_list(length=None):
            collections.append(doc)
        return collections
    
    @collections_router.get("/policy/{policy_id}", response_model=CollectionModel, response_description="Get collection by policy_id")
    async def show_by_policy_id(policy_id: str, request: Request):
        if (collection := await request.app.db['collections'].find_one({"policy_id": policy_id})) is not None:
            return collection

        raise HTTPException(status_code=404, detail=f"Collection [{policy_id}] not found")

    return collections_router