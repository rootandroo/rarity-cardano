from fastapi import APIRouter, Body, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import List

from .models import CollectionModel


def get_collections_router(app):
    collections_router = APIRouter(
        prefix='/collections',
        tags=['collections']
    )

    @collections_router.get("/project/{id}", response_model=List[CollectionModel], response_description="List collections by project")
    async def list_by_project_id(id: str, request: Request):
        collections = []
        for doc in await request.app.db['collections'].find({'project': id}).to_list(length=None):
            collections.append(doc)
        return collections
    
    return collections_router