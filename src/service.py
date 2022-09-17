from graphql_.utils import Project, Collection
import json

policy_id = 'b000e43ed65c89e305bdb5920001558d9f642f3488154b2552a3ad63'
name = 'Ghost Watch'

policy_id = '7a5a5c3757d33c2b2ff0b09405676e61f93d28b5d12805dd3320e31f'
name = 'Crypto Dino'

policy_id = 'd5e6bf0500378d4f0da4e8dde6becec7621cd8cbf5cbb9b87013d4cc'
name = 'SpaceBudz'


def create_project(name):
    project = Project(name)
    return project.save_project()

def create_collection(name, policy_id, project_id):
    collection = Collection(name, policy_id)
    collection.load_collection()
    collection.load_assets()
    new_assets = collection.fetch_assets()
    collection.save_new_assets(new_assets)
    collection.save_collection(project_id)

if __name__ == "__main__":
    project = create_project(name='Clumsy Studios')
    policy_id = '7a5a5c3757d33c2b2ff0b09405676e61f93d28b5d12805dd3320e31f'
    create_collection(name='Ghost Watch', policy_id=policy_id,, project_id=project['_id'])

    policy_id = 'b000e9f3994de3226577b4d61280994e53c07948c8839d628f4a425a'
    create_collection(name='Clumsy Ghosts', policy_id=policy_id, project_id=project['_id'])