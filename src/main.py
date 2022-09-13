from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
import config
import uvicorn 

# from projects.routers import get_projects_router
from projects.models import ProjectModel, UpdateProjectModel
from collections_.models import CollectionModel, UpdateCollectionModel
from assets.models import AssetModel, UpdateAssetModel
from collections_.routers import get_collections_router
from assets.routers import get_assets_router
from routers import get_router

app = FastAPI()


@app.on_event('startup')
async def startup_db_client():
    app.mongodb_client = AsyncIOMotorClient(config.MONGO_URI)
    app.db = app.mongodb_client[config.DB_NAME]

    app.include_router(get_router(app, ProjectModel, UpdateProjectModel, 'project'))
    app.include_router(get_router(app, CollectionModel, UpdateCollectionModel, 'collection'))
    app.include_router(get_router(app, AssetModel, UpdateAssetModel, 'asset'))
    app.include_router(get_collections_router(app))
    app.include_router(get_assets_router(app))

@app.on_event('shutdown')
async def shutdown_db_client():
    app.mongodb_client.close()


if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG_MODE
    )