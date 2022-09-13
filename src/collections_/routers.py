from gc import collect
from fastapi import APIRouter, Body, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import List

from .models import CollectionModel, UpdateCollectionModel


def get_collections_router(app):
    collections_router = APIRouter()

    @collections_router.post('/', response_model=CollectionModel, response_description='Add new collection', tags=['collections'])
    async def create_collections(request: Request, collection: CollectionModel = Body(...)):
        collection = jsonable_encoder(collection)
        new_collection = await request.app.db['collections'].insert_one(collection)
        created_collection = await request.app.db['collections'].find_one(
            {'_id': new_collection.inserted_id}
        )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED, content=created_collection
        )

    @collections_router.get('/', response_model=List[CollectionModel], response_description='List all collections', tags=['collections'])
    async def list_collections(request: Request):
        collections = []
        for doc in await request.app.db['collections'].find().to_list(length=100):
            collections.append(doc)
        return collections

    @collections_router.get('/{id}', response_model=CollectionModel, response_description='Get a collection', tags=['collections'])
    async def show_collection(id: str, request: Request):
        if collection := request.app.db['collections'].find_one({'_id': id}) is not None:
            return collection

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Collection {id} not found')
    
    @collections_router.put('/{id}', response_model=UpdateCollectionModel, response_description='Update a collection', tags=['collections'])
    async def update_collection(
        id: str, request: Request, collection: UpdateCollectionModel = Body(...)
    ):
        collection = {k: v for k, v in collection.dict().items() if v is not None}

        if len(collection) >= 1:
            update_result = await request.app.db['collection'].update_one(
                {"_id": id}, {"$set": collection}
            )
