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
    tx_query = """
        query transactionsByPolicy($policy_id: Hash28Hex, $offset: Int) {
          transactions(
            where: { outputs: { tokens: { asset: { policyId: { _eq: $policy_id } } } } }
            limit: 2500
            order_by: { block: { forgedAt: desc } }
            offset: $offset
          ) {
            hash
            inputs {
              address
              value
              tokens {
                asset {
                  policyId
                  assetName
                }
              }
            }
            outputs {
              address
              value
              tokens {
                asset {
                  policyId
                  assetName
                }
              }
            }
          }
        }
    """

    def __init__(self, name):
        self.name = name
        self.policy_id = str()
        self.last_fetched_tx = str()
        self.assets = dict()
        self.facets = dict()
        self.properties = list()

        self.load_collection()
        self.fetch_assets()
        self.set_properties()
        self.set_facets()

    def save_collection(self):
        print(f'Saving collection [{self.name}].')
        output = dict()
        output['assets'] = self.assets
        output['facets'] = self.facets
        output['policy_id'] = self.policy_id
        output['properties'] = self.properties
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

    def fetch_assets(self):
        if self.assets:
            return

        self.policy_id = input('Enter policy ID: ')

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

    def set_properties(self):
        if self.properties:
            return
        attributes = dict()
        print(f'Setting facets for collection [{self.name}]')
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
            elif value not in self.facets[facet]:
                self.facets[facet][value] = 1
            else:
                self.facets[facet][value] += 1
        if self.facets:
            return
        print('Setting facets.')
        for asset in self.assets.values():
            for property in self.properties:
                value = asset[property]
                if isinstance(value, dict):
                    for inner_property, inner_value in value.items():
                        increment_facet(inner_property, inner_value)
                else:
                    increment_facet(property, value)


    def calc_statistical_rarity(self):
        def calc_rarity_score(prop, val):
            facet_type = 'numericAttributes' if val.isnumeric() else 'stringAttributes'
            frequency = self.facets[f'{facet_type}.{prop}'][val]
            return 1 / (frequency / count)
        count = len(self.assets)
        for asset in self.assets.values():
            rarity_score = 0
            for property in self.properties:
                value = asset[property]
                if isinstance(value, dict):
                    for inner_property, inner_value in value.items():
                        rarity_score += calc_rarity_score(inner_property, inner_value)
                else:
                    rarity_score += calc_rarity_score(property, value)
            asset['rarity'] = rarity_score

    def sort_assets(self):
        self.assets = dict(
            sorted(self.assets.items(), key=lambda asset: -asset[1]['rarity']))

    def fetch_transactions(self):
        offset = 0
        while True:
            variables = {"policy_id": f"{self.policy_id}",
                         "offset": offset * 2500}
            resp = requests.post(
                self.endpoint, json={"query": self.tx_query, "variables": variables})
            if resp.ok:
                txs = resp.json()['data']['transactions']
                if not txs:
                    break
                print('txs found')
                for tx in txs:
                    hash = tx['hash']
                    inputs = tx['inputs']
                    outputs = tx['outputs']
                    # txs have never been fetched
                    if not self.last_fetched_tx:
                        self.last_fetched_tx = hash
                    # pulled all recent txs
                    elif self.last_fetched_tx == hash:
                        self.last_fetched_tx = txs[0]['hash']
                        break
                    
                    # spent_txs = dict()
                    # for input in inputs:
                    #     address = input['address']
                    #     if address not in spent_txs:
                    #         spent_txs[address] = dict()
                    #         spent_txs[address]['value'] = input]

                    print(len(inputs))
                    print(len(outputs))

                    # for input in inputs:
                    #     tokens = input['tokens']
                    #     for token in tokens:
                    #         name = token['asset']['assetName']
                    #         token['asset']['assetName'] = bytes.fromhex(name).decode('ascii')
                    
                    # for output in outputs:
                    #     tokens = output['tokens']
                    #     for token in tokens:
                    #         name = token['asset']['assetName']
                    #         token['asset']['assetName'] = bytes.fromhex(name).decode('ascii')
                            
                    print(json.dumps(inputs, indent=2))
                    print()
                    print(json.dumps(outputs, indent=2))
                break
        def parse_utxo(input, output):
            # determine sale price of NFT
            pass


if __name__ == '__main__':
    name = input('Enter collection name: ')
    collection = Collection(name)
    collection.fetch_transactions()
    # collection.calc_statistical_rarity()
    # collection.sort_assets()
    # collection.save_collection()
