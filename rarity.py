from os.path import exists
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.special import expit
import numpy as np
import requests
import json
import sys


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
        self.fetch_listings()
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
        def append_asset(hit):
            for name, metadata in hit.items():
                self.assets[name] = metadata
                print(f'Appended [{name}] to  assets.')

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
                    if not hits: continue
                    if isinstance(hits, list):
                        for hit in hits:
                            append_asset(hit)
                    elif isinstance(hits, dict):
                        append_asset(hits)
            offset += 1

    # Assets must be set
    def fetch_transactions(self):
        url = f'https://server.jpgstoreapis.com/collection/{self.policy_id}/transactions?'
        params = { "page": 1, "count": 1 }

        resp = requests.get(url, params=params).json()
        num_to_fetch = resp["tot"]
        num_to_fetch -= self.total_tx_count
        if num_to_fetch < 10: return

        params["count"] = num_to_fetch
        print(f'Fetching {num_to_fetch} transactions for collection {self.name}.')
        resp = requests.get(url, params=params).json()

        for tx in resp["transactions"]:
            for asset_name in self.assets:
                asset = self.assets[asset_name]
                if tx["display_name"] == asset["name"]:
                    if asset.get("sales") is None: asset["sales"] = []

                    amount = tx["amount_lovelace"]
                    sales = asset["sales"]
                    if amount not in sales: sales.append(amount)
                    if asset.get('price'): del asset['price']
                    print(json.dumps(sales, indent=2))

        self.total_tx_count = resp["tot"]

    # Assets must be set
    def fetch_listings(self):
        url = f"https://server.jpgstoreapis.com/search/tokens?policyIds=[%22{self.policy_id}%22]"
        params = {
            'saleType': 'default',
            'sortBy': 'recently-listed',
            'verified': 'default',
            'minPrice': "460000000",
            'size': f"1000" }

        resp = requests.get(url, params=params).json()
        for token in resp['tokens']:
            for name in self.assets:
                asset = self.assets[name]
                if asset['name'] == token['display_name']:
                    listing_price = int(token["listing_lovelace"]) / 1_000_000
                    asset['price'] = listing_price

    # Assets must be set
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

    # Assets and properties must be set
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
                if ',' in value: value = value.split()
                if isinstance(value, dict):
                    for inner_property, inner_value in value.items():
                        increment_facet(inner_property, inner_value)
                elif isinstance(value, list):
                    for element in value:
                        increment_facet(property, element)
                else:
                    increment_facet(property, value)


    # Properties, facets, and assets must be set
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
                if ',' in value: value = value.split()
                if isinstance(value, dict):
                    for inner_property, inner_value in value.items():
                        rarity_score += calc_rarity_score(inner_property, inner_value)
                elif isinstance(value, list):
                    for element in value:
                        rarity_score += calc_rarity_score(property, element)
                else:
                    rarity_score += calc_rarity_score(property, value)
            asset['rarity'] = rarity_score

    # rarity unit value must be set
    def set_value_estimates(self):
        model = self.obtain_model()
        for name in self.assets:
            asset = self.assets[name]
            asset['value'] = model(asset['rarity'])

            if not asset.get('price'):
                asset['profit'] = float('-inf')
                continue
            # set profit estimate (price must be set)
            asset['profit'] = asset['value'] - asset['price']

    # rarity scores must be set
    def set_ranks(self):
        names = sorted(self.assets.items(), key=lambda asset: -asset[1].get('rarity'))
        for rank, name in enumerate(names):
            self.assets[name[0]]['rank'] = rank + 1

    def sort_assets(self):
        self.assets = dict(
            sorted(self.assets.items(), key=lambda asset: (
                -asset[1].get('profit') or float('-inf'),
                asset[1].get('price') or float('inf')
                )))

    def obtain_model(self):
        def sigmoid(x, L ,x0, k, b):
            return L * expit(k*(x-x0)) + b

        def create_model(popt):
            def model(x):
                return sigmoid(x, *popt)
            return model

        rarity = []
        prices = []
        for name in self.assets:
            asset = self.assets[name]
            if not asset.get('sales'): continue
            # rarity.extend([asset['rarity']]* len(asset['sales']))
            # prices.extend([sale / 1_000_000 for sale in asset['sales']])

            # average
            # rarity.append(asset['rarity'])
            # prices.append((sum(asset['sales']) / len(asset['sales'])) / 1_000_000)
            
            #max 
            rarity.append(asset['rarity'])
            prices.append(max(asset['sales']) / 1_000_000)
            
        x_data = np.array(rarity)
        y_data = np.array(prices)
        plt.plot(x_data, y_data, 'o')

        popt, pcov = curve_fit(sigmoid, x_data, y_data, p0=[max(y_data), np.median(x_data), 1, min(y_data)], maxfev=10000)
        x_model = np.linspace(min(x_data), max(x_data))
        y_model = sigmoid(x_model, *popt)

        plt.plot(x_model, y_model)
        plt.xscale('log')
        plt.xlabel('rarity')
        plt.ylabel('price')
        plt.grid()
        plt.savefig('graph.png')

        plt.clf()

        plt.imshow(np.log(np.abs(pcov)))
        plt.colorbar()
        plt.savefig('pcov.png')

        return create_model(popt)





if __name__ == '__main__':
    if len(sys.argv) == 1:
        name = input('Enter collection name: ')
    else:
        name = sys.argv[1]
    # name = 'ClumsyGhosts'
    # name = 'Ugly_Bros_Definitive'

    collection = Collection(name)
    collection.calc_statistical_rarity()
    collection.set_value_estimates()
    collection.set_ranks()
    collection.sort_assets()
    collection.save_collection()
