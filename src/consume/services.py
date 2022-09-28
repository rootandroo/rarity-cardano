import requests
import json
import re

from consume.gql_client import GQLClient
import conf

class Project:
    def __init__(self, name):
        self.name = name
        self.id = None

    def get_or_create(self):
        project = {"name": self.name}
        url = f"{conf.DB_ENDPOINT}/project"
        resp = requests.post(url, json=project)
        if not resp.ok:
            url = f"{conf.DB_ENDPOINT}/project/name/{self.name}"
            resp = requests.get(url)
        self.id = resp.json()['_id']


class Collection:
    client = GQLClient()

    def __init__(self, name, policy_id, project_id):
        self.id = None
        self.name = name
        self.policy = policy_id
        self.project = project_id

        self.properties = []
        self.facets = {}
        self.tx_count = 0

        self.assets = []
        self.new_assets = []

    def load_collection(self):
        url = f'{conf.DB_ENDPOINT}/collection/policy/{self.policy}'
        resp = requests.get(url)        
        if not resp.ok: return 
        collection = resp.json()
        
        self.id = collection['_id']
        self.policy = collection['policy_id']
        self.properties = collection['properties']
        self.facets = collection['facets']
        self.tx_count = collection['tx_count']

        print(f'Loaded collection [{self.name}].')

    def load_assets(self):
        url = f'{conf.DB_ENDPOINT}/asset/policy/{self.policy}'
        resp = requests.get(url)
        if not resp.ok: return 

        self.assets += resp.json()
        print(f'Loaded assets for collection [{self.name}].')

    def append_asset(self, hit):
        for name, metadata in hit.items():
            if any(name == asset["name"] for asset in self.assets): continue

            asset = {"name": name, "metadata": metadata, "collection": self.policy}
            self.assets.append(asset)
            self.new_assets.append(asset)

    def fetch_assets(self):
        onchain_count = self.client.get_asset_count(self.policy)
        if len(self.assets) == int(onchain_count):
            return

        print(f'Fetching assets for collection [{self.name}]')
        offset = 0
        while True:
            print(f'    Fetched {len(self.assets)}/{onchain_count} assets.')
            txs = self.client.get_assets(self.policy, offset * 2500)
            if not txs:
                break
            for tx in txs:
                tx_metadata = tx["metadata"]
                if not tx_metadata:
                    continue
                hits = tx_metadata[0]["value"].get(self.policy)
                if isinstance(hits, list):
                    for hit in hits:
                        self.append_asset(hit)
                elif isinstance(hits, dict):
                    self.append_asset(hits)
            offset += 1    

    def set_properties(self):
        attributes = dict()
        print(f'Setting properties for rarity calculation for collection [{self.name}]')
        for asset in self.assets:
            metadata = asset['metadata']
            for key, value in metadata.items():
                if key not in attributes:
                    attributes[key] = list()
                if len(attributes[key]) < 2:
                    attributes[key].append(value)

        print(f' {(json.dumps(attributes, indent=2))}')
        print(f' {[key for key in list(attributes.keys()) if key not in self.properties]}')
        properties = input('    Enter list of traits to include:\n')
        properties, _ = re.subn("[\[\]\']", '', properties)
        properties = properties.split(', ')
        print(properties)
        resp = input('    Include Keys? Y/N: ')
        if resp == "Y":
            self.properties += properties
        else:
            return

    def set_facets(self):
        def increment_facet(property, value):
            if property not in self.facets:
                self.facets[property] = {}

            if value not in self.facets[property]:
                self.facets[property][value] = 1
            else:
                self.facets[property][value] += 1
        print(f'Setting facets for collection [{self.name}]')
        for asset in self.assets:
            for property in self.properties:
                metadata = asset['metadata']
                value = self.get_value(metadata, property)
                if isinstance(value, dict):
                    for inner_property, inner_value in value.items():
                        increment_facet(inner_property, inner_value)
                elif isinstance(value, list):
                    for element in value:
                        increment_facet(property, element)
                else:
                    increment_facet(property, value)

    def calc_string_stat_rarity(self):
        print(f'Calculating string statistical rarity for collection [{self.name}]')
        def calc_rarity_score(prop, val):
            frequency = self.facets[prop][val]
            return 1 / (frequency / count)
        count = len(self.assets)
        for asset in self.assets:
            rarity_score = 0
            metadata = asset['metadata']
            for property in self.properties:
                value = self.get_value(metadata, property)
                if isinstance(value, dict):
                    for inner_property, inner_value in value.items():
                        rarity_score += calc_rarity_score(inner_property, inner_value)
                elif isinstance(value, list):
                    for element in value:
                        rarity_score += calc_rarity_score(property, element)
                else:
                    rarity_score += calc_rarity_score(property, value)
            asset['rarity'] = rarity_score

    def get_value(self, metadata, property):
        value = metadata.get(property) or "None"
        if ',' in value: value = value.split()
        return value

    def save(self):
        collection = {
            "name": self.name,
            "policy_id": self.policy,
            "tx_count": self.tx_count,
            "properties": self.properties,
            "facets": self.facets,
            "project": self.project
        }
        url = f'{conf.DB_ENDPOINT}/collection'
        requests.post(url, json=collection)
        print(f'Saved collection [{self.name}]')

    def update(self):
        collection = {
            "tx_count": self.tx_count,
            "properties": self.properties,
            "facets": self.facets,
        }
        url = f'{conf.DB_ENDPOINT}/collection/{self.id}'
        requests.put(url, json=collection)
        print(f'Updated collection [{self.name}]')

    def save_new_assets(self):
        url = f'{conf.DB_ENDPOINT}/asset/bulk/'        
        resp = requests.post(url, json=self.new_assets)

        print(f'Saved new assets for collection [{self.name}]')

    def update_assets(self):
        url = f'{conf.DB_ENDPOINT}/asset/bulk/'
        requests.put(url, json=self.assets)
        print(f'Updated assets for collection [{self.name}]')


def create_collection(project, policy):
    collection = Collection("Clumsy Ghosts", policy, project.id)
    collection.fetch_assets()

    collection.set_properties()
    collection.set_facets()
    collection.save()

    collection.calc_string_stat_rarity()
    collection.save_new_assets()
    return collection

if __name__ == "__main__":
    # Entirely New Project
    project = Project("Clumsy Studios")
    project.get_or_create()

    policy_id = "b000e9f3994de3226577b4d61280994e53c07948c8839d628f4a425a"

    # Update Existing Collection
    collection = Collection("Clumsy Ghosts", policy_id, project.id)
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

