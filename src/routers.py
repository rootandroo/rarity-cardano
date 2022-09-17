from fastapi import APIRouter, Body, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import List


def get_router(app, Model, UpdateModel, name):
    db_name = f'{name}s'
    
    router = APIRouter(
        prefix=f'/{name}',
        tags=[db_name]
    )

    @router.post("/", response_model=Model, response_description=f"Add new {name}")
    async def create(request: Request, object: Model = Body(...)):
        object = jsonable_encoder(object)
        new_object = await request.app.db[db_name].insert_one(object)
        created_object = await request.app.db[db_name].find_one(
            {"_id": new_object.inserted_id}
        )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED, content=created_object
        )
    create.__name__ = f'create_{name}'

    @router.get("/", response_model=List[Model], response_description=f"List all {name}s")
    async def list(request: Request):
        objects = []
        for doc in await request.app.db[db_name].find().to_list(length=100):
            objects.append(doc)
        return objects
    list.__name__ = f'list_{name}s'

    @router.get("/{id}", response_model=Model, response_description=f"Get a single {name}")
    async def show(id: str, request: Request):
        if (object := await request.app.db[db_name].find_one({"_id": id})) is not None:
            return object

        raise HTTPException(status_code=404, detail=f"{name} {id} not found")
    show.__name__ = f'show_{name}'

    @router.put("/{id}", response_model=UpdateModel, response_description=f"Update a {name}")
    async def update(
        id: str, request: Request, object: UpdateModel = Body(...)
    ):
        object = {k: v for k, v in object.dict().items() if v is not None}

        if len(object) >= 1:
            update_result = await request.app.db[db_name].update_one(
                {"_id": id}, {"$set": object}
            )

            if update_result.modified_count == 1:
                if  (updated_object := await request.app.db[db_name].find_one({'id': id})) is not None:
                    return updated_object 

        if (existing_object := await request.app.db[db_name].find_one({'_id': id})) is not None:
            return existing_object
        
        raise HTTPException(status_code=404, detail=f'{name} {id} not found')
    update.__name__ = f'update_{name}'

    @router.delete('/{id}', response_model= Model, response_description=f'Delete a {name}')
    async def delete(id: str, request: Request, response: Response):
        delete_result = await request.app.db[db_name].delete_one({'_id': id})

        if delete_result.deleted_count == 1:
            response.status_code = status.HTTP_204_NO_CONTENT
            return response

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'{name} {id} not found')
    delete.__name__ = f'delete_{name}'
    
    return router