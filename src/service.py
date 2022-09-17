from graphql_.utils import Project, Collection
import json

def create_project(name):
    project = Project(name)
    return project.save_project()

def create_collection(name, policy_id, project_id):
    collection = Collection(name, policy_id)
    collection.load_collection()
    collection.load_assets()
    new_assets = collection.fetch_assets()
    collection.set_properties()
    collection.set_facets()
    collection.save_new_assets(new_assets)
    collection.save_collection(project_id)
    collection.calc_statistical_rarity()
    collection.bulk_update_assets()

if __name__ == "__main__":
    project = create_project(name='Clumsy Studios')
    policy_id = 'b000e9f3994de3226577b4d61280994e53c07948c8839d628f4a425a'
    create_collection(name='Clumsy Ghosts', policy_id=policy_id, project_id=project['_id'])