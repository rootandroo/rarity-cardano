from os.path import exists
import requests
import json


class Collection():
    endpoint = "https://graphql-api.mainnet.dandelion.link/"
    assets_query = """
        query metadataByPolicy($policy_id: Hash28Hex, $offset: Int) {
          transactions(
            where: { mint: { asset: { policyId: { _eq: $policy_id } } } }
            limit: 2500
            offset: $offset
          ) {
            metadata {
              value
            }
          }
        }
    """

    def __init__(self, name):
        self.name = name
        self.policy_id = str()
        self.total_tx_count = 0
        self.assets = dict()
        self.facets = dict()
        self.properties = list()
        self.rarity_unit_value = 0

        self.load_collection()
        self.fetch_assets()
        self.fetch_transactions()
        self.set_properties()
        self.set_facets()

    def save_collection(self):
        print(f'Saving collection [{self.name}].')
        output = dict()
        output['assets'] = self.assets
        output['facets'] = self.facets
        output['policy_id'] = self.policy_id
        output['properties'] = self.properties
        output['tx_count'] = self.total_tx_count
        with open(f'collections/{self.name}.json', 'w') as file:
            json.dump(output, file, indent=2)

    def load_collection(self):
        if not exists(f'collections/{self.name}.json'):
            return

        print(f'Loading collection [{self.name}].')
        with open(f'collections/{self.name}.json') as file:
            input = json.load(file)
        self.assets = input['assets']
        self.facets = input['facets']
        self.policy_id = input['policy_id']
        self.properties = input['properties']
        self.total_tx_count = input['tx_count']

    def fetch_assets(self):
        if self.policy_id: return
        self.policy_id = input('Enter policy ID: ')

        if self.assets: return

        print(f'Fetching assets for collection [{self.name}]')
        offset = 0
        while True:
            variables = {"policy_id": f"{self.policy_id}",
                         "offset": offset * 2500}
            resp = requests.post(
                self.endpoint, json={"query": self.assets_query, "variables": variables})
            if resp.ok:
                txs = resp.json()['data']['transactions']
                if not txs:
                    break

                for tx in txs:
                    tx_metadata = tx['metadata']
                    if not tx_metadata:
                        continue
                    hits = tx_metadata[0]['value'].get(self.policy_id)
                    if not hits:
                        continue
                    for name, metadata in hits.items():
                        self.assets[name] = metadata
                        print(f'Appended [{name}] to  assets.')

            offset += 1

    # Assets must be set
    def fetch_transactions(self):
        url = f'https://server.jpgstoreapis.com/collection/{self.policy_id}/transactions?'
        params = { "page": 1, "count": 1 }

        resp = requests.get(url, params=params).json()
        num_to_fetch = resp["tot"]
        num_to_fetch -= self.total_tx_count

        params["count"] = num_to_fetch
        print(f'Fetching {num_to_fetch} transactions for collection {self.name}.')
        resp = requests.get(url, params=params).json()

        for tx in resp["transactions"]:
            for asset_name in self.assets:
                metadata = self.assets[asset_name]
                if tx["display_name"] == metadata["name"]:
                    if metadata.get("sales") is None: metadata["sales"] = []

                    amount = tx["amount_lovelace"]
                    sales = metadata["sales"]
                    if amount not in sales: sales.append(amount)
                    print(json.dumps(sales, indent=2))

        self.total_tx_count = resp["tot"]

    def set_properties(self):
        if self.properties:
            return
        attributes = dict()
        print(f'Setting properties for collection [{self.name}]')
        for asset in self.assets.values():
            for key, value in asset.items():
                if key not in attributes:
                    attributes[key] = list()
                if len(attributes[key]) < 3:
                    attributes[key].append(value)
        print(json.dumps(attributes, indent=2))

        num_keys = int(input('Enter number of keys to include: '))
        for i in range(num_keys):
            self.properties.append(input('Enter key: '))

    def set_facets(self):
        def increment_facet(property, value):
            facet_type = 'numericAttributes' if value.isnumeric() else 'stringAttributes'
            facet = f'{facet_type}.{property}'
            if facet not in self.facets:
                self.facets[facet] = {}
            
            if value not in self.facets[facet]:
                self.facets[facet][value] = 1
            else:
                self.facets[facet][value] += 1
        if self.facets:
            return
        print('Setting facets.')
        for asset in self.assets.values():
            for property in self.properties:
                value = asset.get(property) or "None"
                if isinstance(value, dict):
                    for inner_property, inner_value in value.items():
                        increment_facet(inner_property, inner_value)
                else:
                    increment_facet(property, value)


    # Properties and facets must be set
    def calc_statistical_rarity(self):
        def calc_rarity_score(prop, val):
            facet_type = 'numericAttributes' if val.isnumeric() else 'stringAttributes'
            frequency = self.facets[f'{facet_type}.{prop}'][val]
            return 1 / (frequency / count)
        count = len(self.assets)
        for asset in self.assets.values():
            rarity_score = 0
            for property in self.properties:
                value = asset.get(property) or "None"
                if isinstance(value, dict):
                    for inner_property, inner_value in value.items():
                        rarity_score += calc_rarity_score(inner_property, inner_value)
                else:
                    rarity_score += calc_rarity_score(property, value)
            asset['rarity'] = rarity_score

    # rarity and sales must be set
    def calc_rarity_unit_value(self):
        rarity_score_total =  0
        lovelace_total = 0
        for name in self.assets:
            asset = self.assets[name]

            sales = asset.get('sales')
            if sales:
                rarity_score_total += asset['rarity']
                # lovelace_total += sum(sales) / len(sales)
                lovelace_total += sales[0]
        self.rarity_unit_value = ( lovelace_total / rarity_score_total ) / 1_000_000
    
    # rarity unit value must be set
    def set_value_estimate(self):
        for name in self.assets:
            asset = self.assets[name]
            asset['value'] = self.rarity_unit_value * asset['rarity']

    def sort_assets(self):
        self.assets = dict(
            sorted(self.assets.items(), key=lambda asset: -asset[1]['rarity']))
            



if __name__ == '__main__':
    name = input('Enter collection name: ')
    collection = Collection(name)
    collection.calc_statistical_rarity()
    collection.calc_rarity_unit_value()
    collection.set_value_estimate()
    collection.sort_assets()
    collection.save_collection()
