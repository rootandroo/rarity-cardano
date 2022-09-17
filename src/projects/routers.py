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
    
    return projects_router