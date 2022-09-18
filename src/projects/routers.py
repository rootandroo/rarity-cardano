from fastapi import APIRouter, Body, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import List

from .models import ProjectModel, UpdateProjectModel
from routers import get_router

def get_projects_router(app):
    app.include_router(get_router(app, ProjectModel, UpdateProjectModel, 'project'))

    projects_router = APIRouter(
        prefix='/project',
        tags=['projects']
    )
    
    @projects_router.get("/name/{name}", response_model=ProjectModel, response_description=f"Get a single project by name")
    async def show_by_name(name: str, request: Request):
        if (project := await request.app.db['projects'].find_one({"name": name})) is not None:
            return project

        raise HTTPException(status_code=404, detail=f"{name} not found")
    return projects_router