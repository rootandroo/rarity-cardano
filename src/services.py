import collections
import requests
import json

from graphql_.utils import GQLClient
import conf

class Project:
    def __init__(self, name):
        self.name = name
        
    def get_project(self):
        print(f"Fetching project [{self.name}] from database ...")
        url = f"{conf.DB_ENDPOINT}/project/name/{self.name}"
        resp = requests.get(url, json={"name": self.name})
        if resp.ok:
            return resp.json()

    def save_project(self):
        print(f"Inserting project [{self.name}] into database ...")
        url = f"{conf.DB_ENDPOINT}/project/"
        resp = requests.post(url, json={"name": self.name})
        return resp.json()


class Collection:
    client = GQLClient()


    def __init__(self, name, policy_id, project_id):
        # Collection
        self.name = name
        self.project_id = project_id
        self.policy_id = policy_id
        self.tx_count = 0
        self.properties = []
        self.facets = {}

        # Assets
        self.assets = []
        self.new_assets = []

    def fetch_assets(self):
        """
        Check for new assets onchain and store them in self.new_assets
        """
        def append_asset(asset):
            for name, metadata in asset.items():
                if any(asset["name"] == name for asset in self.assets):
                    continue
                asset = {
                    "name": name,
                    "metadata": metadata,
                    "collection": self.policy_id,
                }
                self.assets.append(asset)
                self.new_assets.append(asset)

        onchain_count = Collection.client.get_asset_count(self.policy_id)
        if len(self.assets) == int(onchain_count): return

        print(f"Fetching assets for collection [{self.name}] ...")
        # Query onchain metadata until all the new assets are in working memory
        offset = 0
        while len(self.assets) != int(onchain_count):
            print(f"    Fetched {len(self.assets)}/{onchain_count} assets")
            txs = Collection.client.get_assets(self.policy_id, offset * 2500)
            if not txs:
                break

            for tx in txs:
                tx_metadata = tx["metadata"]
                if not tx_metadata:
                    continue

                hits = tx_metadata[0]["value"].get(self.policy_id)
                if not hits:
                    continue

                if isinstance(hits, list):
                    for hit in hits:
                        append_asset(hit)
                elif isinstance(hits, dict):
                    append_asset(hits)
            offset += 1

    
    def load_collection(self):
        """
        Loads collection from API into Collection Object.
        """
        url = f"{conf.DB_ENDPOINT}/collection/policy/{self.policy_id}"
        resp = requests.get(url)
        if not resp.ok:
            return

        collection = resp.json()
        self.name = collection["name"]
        self.tx_count = collection["tx_count"]
        self.properties = collection["properties"]
        self.facets = collection["facets"]
        print(f"    Loaded collection [{self.name}] into memory.")


    def load_assets(self):
        """
        Loads assets from API into Collection Object.
        """
        url = f"{conf.DB_ENDPOINT}/asset/policy/{self.policy_id}"
        resp = requests.get(url)
        if not resp.ok:
            return

        for asset in resp.json():
            self.assets.append(
                {
                    "name": asset["name"],
                    "metadata": asset["metadata"],
                    "collection": asset["collection"],
                }
            )
        print(f"    Loaded {len(self.assets)} assets into memory.")


    def save_collection(self):
        """
        Saves collection if collection properties have been altered.
        """
        url = f"{conf.DB_ENDPOINT}/collection/"
        collection = {
            "name": self.name,
            "tx_count": self.tx_count,
            "properties": self.properties,
            "policy_id": self.policy_id,
            "facets": self.facets,
            "project": self.project_id,
        }
        requests.post(url, json=collection)


    def save_new_assets(self):
        if not self.new_assets: return

        print(f"Inserting {len(self.new_assets)} assets to database ...")
        url = f"{conf.DB_ENDPOINT}/asset/bulk/"
        requests.post(url, json=self.new_assets)


    def bulk_update_assets(self):
        """
        Update assets if their metadata or rarity scores were changed.
        """
        print(f"Bulk updating {len(self.assets)} assets ...")
        url = f"{conf.DB_ENDPOINT}/asset/bulk/"
        requests.put(url, json=self.assets)


    def set_facets(self):
        """
        Set facets for evaulating rarity if additional assets were added or if 
        assets' metadata were changed. 
        """
        def increment_facet(property, value):
            facet_type = (
                "numericAttributes" if value.isnumeric() else "stringAttributes"
            )
            facet = f"{facet_type}.{property}"
            if facet not in self.facets:
                self.facets[facet] = {}

            if value not in self.facets[facet]:
                self.facets[facet][value] = 1
            else:
                self.facets[facet][value] += 1

        print("Setting facets ...")
        for asset in self.assets:
            metadata = asset["metadata"]
            for property in self.properties:
                value = self.get_value(metadata, property)
                if isinstance(value, dict):
                    for inner_property, inner_value in value.items():
                        increment_facet(inner_property, inner_value)
                elif isinstance(value, list):
                    for element in value:
                        increment_facet(property, element)
                else:
                    increment_facet(property, value)


    def set_properties(self):
        """
        Set properties for evaulating rarity if additional assets were added or if 
        assets' metadata were changed
        """
        attributes = dict()
        print(f"Setting properties for collection [{self.name}] ...")
        for asset in self.assets:
            metadata = asset["metadata"]
            for key, value in metadata.items():
                if key not in attributes:
                    attributes[key] = list()
                if len(attributes[key]) < 2:
                    attributes[key].append(value)
        print(json.dumps(attributes, indent=2))
        print(list(attributes.keys()))

        num_keys = int(input("Enter number of keys to include: "))
        for i in range(num_keys):
            self.properties.append(input("Enter key: "))


    def calc_statistical_rarity(self):
        print(f"Calculating string statistical rarity for collection [{self.name}] ...")

        def calc_rarity_score(prop, val):
            facet_type = "numericAttributes" if val.isnumeric() else "stringAttributes"
            frequency = self.facets[f"{facet_type}.{prop}"][val]
            return 1 / (frequency / count)

        count = len(self.assets)
        for asset in self.assets:
            rarity_score = 0
            metadata = asset["metadata"]
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
            asset["rarity"] = rarity_score


    # Helper function to extract value given a trait
    def get_value(self, metadata, property):
        value = metadata.get(property) or "None"
        if "," in value:
            value = value.split()
        return value



def find_or_create_project(name):
    project = Project(name)
    instance = project.get_project()
    if not instance: 
        instance = project.save_project()
    return instance

def update_collection(collection):
    collection.set_properties()
    collection.set_facets()
    collection.save_collection()
    collection.calc_statistical_rarity()
    collection.bulk_update_assets()
    return collection

def new_collection(name, policy_id, project_id):
    collection = Collection(name, policy_id, project_id)
    collection.fetch_assets()
    collection.save_new_assets()
    collection.set_properties()
    collection.set_facets()
    collection.save_collection()
    collection.calc_statistical_rarity()
    collection.bulk_update_assets()
    return collection

if __name__ == "__main__":
    policy_id = 'b000e9f3994de3226577b4d61280994e53c07948c8839d628f4a425a'

    # New or Existing Project
    project = find_or_create_project(name='Clumsy Studios')

