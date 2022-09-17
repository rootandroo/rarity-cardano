from gql import Client
from gql.transport.requests import RequestsHTTPTransport
import requests

from . import queries
import conf


class GQLClient:
    def __init__(self):
        transport = RequestsHTTPTransport(url=conf.ENDPOINT)
        self._client = Client(transport=transport)

    # Determine number of assets onchain for a given policy_id
    def get_asset_count(self, policy_id):
        params = {"policy_id": policy_id}
        resp = self._client.execute(queries.asset_count, variable_values=params)
        return resp["assets_aggregate"]["aggregate"]["count"]

    # Obtain onchain assets for a given policy_id 
    def get_assets(self, policy_id, offset):
        params = {"policy_id": policy_id, "offset": offset}
        resp = self._client.execute(queries.metadata, variable_values=params)
        return resp["transactions"]


class Project:
    def __init__(self, name):
        self.name = name

    def save_project(self):
        print(f"Inserting project [{self.name}] into database")
        url = f"{conf.DB_ENDPOINT}/project/"
        resp = requests.post(url, json={"name": self.name})
        return resp.json()


class Collection:
    client = GQLClient()

    def __init__(self, name, policy_id):
        self.name = name
        self.policy_id = policy_id
        self.tx_count = 0
        self.assets = {}
        self.properties = []
        self.facets = {}


    def fetch_assets(self):
        new_assets = []

        def append_asset(asset):
            for name, metadata in asset.items():
                if name in self.assets: continue
                self.assets[name] = metadata
                new_assets.append({
                    "name": name,
                    "metadata": metadata,
                    "collection": self.policy_id
                })

        onchain_count = Collection.client.get_asset_count(self.policy_id)

        print(f"Fetching assets for collection [{self.name}]")
        
        # Query onchain metadata until all the new assets are in working memory
        offset = 0
        while len(self.assets) != int(onchain_count):
            print(f'    Fetched {len(self.assets)}/{onchain_count} assets')
            txs = Collection.client.get_assets(self.policy_id, offset * 2500)
            if not txs: break

            for tx in txs:
                tx_metadata = tx["metadata"]
                if not tx_metadata: continue

                hits = tx_metadata[0]['value'].get(self.policy_id)
                if not hits: continue

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
        if not resp.ok: return

        collection = resp.json()
        self.name = collection["name"]
        self.tx_count = collection["tx_count"]
        self.properties = collection["properties"]
        self.facets = collection["facets"]
        print(f"Loaded collection [{self.name}] into memory.")

    def save_collection(self, project_id):
        url = f"{conf.DB_ENDPOINT}/collection/"
        collection = {
            "name": self.name,
            "tx_count": self.tx_count,
            "properties": self.properties,
            "policy_id": self.policy_id,
            "facets": self.facets,
            "project": project_id
        }
        requests.post(url, json=collection)
        
    def load_assets(self):
        url = f"{conf.DB_ENDPOINT}/asset/policy/{self.policy_id}"
        resp = requests.get(url)
        if not resp.ok: return
        
        for asset in resp.json():
            self.assets[asset["name"]] = asset["metadata"]
        print(f"Loaded {len(self.assets)} assets into memory.")

    # Bulk save new assets
    def save_new_assets(self, assets):
        if not assets: return
        print(f'Inserting {len(assets)} assets to database')
        url = f"{conf.DB_ENDPOINT}/asset/bulk/"
        requests.post(url, json=assets)


if __name__ == "__main__":
    pass
