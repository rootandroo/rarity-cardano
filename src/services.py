import requests
import json

from graphql_.utils import GQLClient
import conf

class Project:
    def __init__(self, name):
        self.name = name

    def save_project(self):
        print(f"    Inserting project [{self.name}] into database ...")
        url = f"{conf.DB_ENDPOINT}/project/"
        resp = requests.post(url, json={"name": self.name})
        return resp.json()


class Collection:
    client = GQLClient()

    def __init__(self, name, policy_id):
        self.name = name
        self.policy_id = policy_id
        self.tx_count = 0
        self.assets = []
        self.properties = []
        self.facets = {}
        self.data = {}

    def fetch_assets(self):
        new_assets = []

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
                new_assets.append(asset)

        onchain_count = Collection.client.get_asset_count(self.policy_id)

        if len(self.assets) == int(onchain_count):
            return

        print(f"    Fetching assets for collection [{self.name}] ...")
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
        return new_assets

    def load_collection(self):
        url = f"{conf.DB_ENDPOINT}/collection/policy/{self.policy_id}"
        resp = requests.get(url)
        if not resp.ok:
            return

        collection = resp.json()
        self.data = collection
        self.name = collection["name"]
        self.tx_count = collection["tx_count"]
        self.properties = collection["properties"]
        self.facets = collection["facets"]
        print(f"    Loaded collection [{self.name}] into memory.")

    def save_collection(self, project_id):
        if self.data:
            return

        url = f"{conf.DB_ENDPOINT}/collection/"
        collection = {
            "name": self.name,
            "tx_count": self.tx_count,
            "properties": self.properties,
            "policy_id": self.policy_id,
            "facets": self.facets,
            "project": project_id,
        }
        requests.post(url, json=collection)

    def load_assets(self):
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

    # Bulk save new assets
    def save_new_assets(self, assets):
        if not assets:
            return
        print(f"    Inserting {len(assets)} assets to database ...")
        url = f"{conf.DB_ENDPOINT}/asset/bulk/"
        requests.post(url, json=assets)

    def bulk_update_assets(self):
        print(f"    Bulk updating {len(self.assets)} assets ...")
        url = f"{conf.DB_ENDPOINT}/asset/bulk/"
        requests.put(url, json=self.assets)

    def set_facets(self):
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

        if self.facets:
            return

        print(" Setting facets ...")
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

    # Helper function to extract value given a trait
    def get_value(self, metadata, property):
        value = metadata.get(property) or "None"
        if "," in value:
            value = value.split()
        return value

    # Set properties to include when evaluating rarity
    def set_properties(self):
        if self.properties:
            return

        attributes = dict()
        print(f"    Setting properties for collection [{self.name}] ...")
        for asset in self.assets:
            metadata = asset["metadata"]
            for key, value in metadata.items():
                if key not in attributes:
                    attributes[key] = list()
                if len(attributes[key]) < 2:
                    attributes[key].append(value)
        print(json.dumps(attributes, indent=2))
        print(attributes.keys())

        num_keys = int(input("  Enter number of keys to include: "))
        for i in range(num_keys):
            self.properties.append(input("  Enter key: "))

    def calc_statistical_rarity(self):
        print(f"    Calculating string statistical rarity for collection [{self.name}] ...")

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