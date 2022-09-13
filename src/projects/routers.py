from fastapi import APIRouter, Body, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import List

from .models import ProjectModel, UpdateProjectModel


def get_projects_router(app):
    projects_router = APIRouter()

    @projects_router.post("/", response_model=ProjectModel, response_description="Add new project", tags=['projects'])
    async def create_project(request: Request, project: ProjectModel = Body(...)):
        project = jsonable_encoder(project)
        new_project = await request.app.db["projects"].insert_one(project)
        created_project = await request.app.db["projects"].find_one(
            {"_id": new_project.inserted_id}
        )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED, content=created_project
        )

    @projects_router.get("/", response_model=List[ProjectModel], response_description="List all projects", tags=['projects'])
    async def list_projects(request: Request):
        projects = []
        for doc in await request.app.db["projects"].find().to_list(length=100):
            projects.append(doc)
        return projects

    @projects_router.get("/{id}", response_model=ProjectModel, response_description="Get a single project", tags=['projects'])
    async def show_project(id: str, request: Request):
        if project := request.app.db["projects"].find_one({"_id": id}) is not None:
            return project

        raise HTTPException(status_code=404, detail=f"Project {id} not found")

    @projects_router.put("/{id}", response_model=UpdateProjectModel, response_description="Update a project", tags=['projects'])
    async def update_project(
        id: str, request: Request, project: UpdateProjectModel = Body(...)
    ):
        project = {k: v for k, v in project.dict().items() if v is not None}

        if len(project) >= 1:
            update_result = await request.app.db["projects"].update_one(
                {"_id": id}, {"$set": project}
            )

            if update_result.modified_count == 1:
                if  (updated_project := await request.app.db['projects'].find_one({'id': id})) is not None:
                    return updated_project 

        if (existing_project := await request.app.db['projects'].find_one({'_id': id})) is not None:
            return existing_project
        
        raise HTTPException(status_code=404, detail=f'Project {id} not found')

    @projects_router.delete('/{id}', response_model= ProjectModel, response_description='Delete a project', tags=['projects'])
    async def delete_project(id: str, request: Request, response: Response):
        delete_result = await request.app.db['projects'].delete_one({'_id': id})

        if delete_result.deleted_count == 1:
            response.status_code = status.HTTP_204_NO_CONTENT
            return response

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Project {id} not found')
    
    return projects_router