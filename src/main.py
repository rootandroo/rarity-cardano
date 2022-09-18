from fastapi import FastAPI
import uvicorn 

from projects.routers import get_projects_router
from collections_.routers import get_collections_router
from assets.routers import get_assets_router
from database import init_db
import conf


app = FastAPI()


@app.on_event('startup')
async def startup_db_client():
    await init_db(app)
    app.include_router(get_projects_router(app))
    app.include_router(get_collections_router(app))
    app.include_router(get_assets_router(app))


@app.on_event('shutdown')
async def shutdown_db_client():
    app.mongodb_client.close()


if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host=conf.HOST,
        port=conf.PORT,
        reload=conf.DEBUG_MODE
    )