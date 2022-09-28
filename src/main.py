from fastapi import FastAPI
from projects.routers import get_projects_router
from collections_.routers import get_collections_router
from assets.routers import get_assets_router
from database import init_db

from consume.clumsy import update_clumsy_hidden, fetch_all_scripts
from consume.services import Project, Collection, create_collection
import asyncio 
import json

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
    # Update Clumsy
    # policy = "b000e9f3994de3226577b4d61280994e53c07948c8839d628f4a425a"
    # update_clumsy_hidden(policy)

    # Add New Collection
    # project = Project("Clumsy Studios")
    # project.get_or_create()
    # policy = "b00041d7dc086d33e0f7777c4fccaf3ef06720543d4ff4e750d8f123"
    # collection = create_collection(project, policy)

    project = Project("Clumsy Studios")
    project.get_or_create()
    policy = "b00041d7dc086d33e0f7777c4fccaf3ef06720543d4ff4e750d8f123"
    collection = Collection("Clumsy Valley", policy, project.id)
    collection.load_collection()    
    collection.load_assets()
    collection.fetch_assets()

    if collection.new_assets:
        collection.save_new_assets()
        collection.set_properties()        
        collection.set_facets()
        collection.update()        

        collection.calc_string_stat_rarity()
        collection.update_assets()