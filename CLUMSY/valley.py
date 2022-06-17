import json
import os
import csv

def parse_file(filename, stats):
    with open(filename) as csv_file:
        csv_reader = csv.DictReader(csv_file)
        trait = csv_reader.fieldnames[0]
        
        for row in csv_reader:
            value = row[trait]
            stat = row['Stat']
            boost = row['Count']
            biome = row.get('Biome')
            biome_boost = row.get('Biome Roll modifier')

            key = f'{trait.lower()}.{value}'

            if not stat: continue
            if stat == "smart": stat = 'smarts'
            stats[key] = {}
            stats[key][stat] = int(boost)

            if not biome: continue

            stats[key][biome] = int(biome_boost)

# Loop through .csv files to populate stats
def obtain_stats():
    stats = {}
    for filename in os.listdir('.'):
        if filename.endswith(".csv"):
            parse_file(filename, stats)
    return stats

def load_collection():
    with open('valley.json') as file:
        output = json.load(file)
        return output

def set_assets_stats(stats, collection):
    for name in collection['assets']:
        asset = collection['assets'][name]
        asset['stats'] = {}
        for trait in asset:
            if trait not in collection['properties']: continue
            
            value = asset.get(trait) or "None"
            key = f'{trait}.{value}'
            if key in stats:
                stat_keys = list(stats[key].keys())
                skill = stat_keys[0]
                if skill not in asset['stats']:
                    asset['stats'][skill] = stats[key][skill]
                else:
                    asset['stats'][skill] += stats[key][skill]

                if len(stat_keys) != 2: continue
                biome = stat_keys[1]
                biome_skill = f'{skill}.{biome}'
                if biome_skill not in asset['stats']:
                    asset['stats'][biome_skill] = stats[key][biome]
                else:
                    asset['stats'][biome_skill] += stats[key][biome]

        # apply multiplier
        multiplier = determine_multiplier(asset['rank'])
        for stat in asset['stats']:
            if '.' in stat : continue
            asset['stats'][stat] *= multiplier

        # set stat_total and unit_stat_cost
        asset_stat_total = 0
        for stat in asset['stats']:
            if stat in ['speed', 'luck', 'stamina']:
            # if any(substr in stat for substr in ['speed', 'luck', 'stamina']):
                asset_stat_total += asset['stats'][stat]
        asset['stat_total'] = asset_stat_total
        if not asset.get('price'): continue
        asset['unit_cost'] = asset["price"] / asset["stat_total"]

def sort_assets(collection):
    collection['assets'] = dict(
        sorted(collection['assets'].items(), key=lambda asset: (
            -asset[1].get('stat_total'), 
            # asset[1].get('unit_cost') or float('inf')
            )))
    

def save_collection(collection):
    with open('valley.json', 'w') as file:
        json.dump(collection, file, indent=2)


def determine_multiplier(rank):
    multipliers = {
        (1, 1) : 3,
        (2, 100):  2.25,
        (101, 250): 2.125,
        (251, 500):  2,
        (501, 1000): 1.75,
        (1001, 2500): 1.5,
        (2501, 5000): 1.25,
        (5000, 10000): 1.125 }
    for min, max in multipliers.keys():
        if rank >= min and rank <= max:
            vector = multipliers[(min, max)]
            return vector

def display(collection):
    for name in collection['assets']:
        asset = collection['assets'][name]
        if not asset.get('price'): continue
        if asset.get('price') > 700: continue
        unit_cost = asset["price"] / asset["stat_total"]
        if unit_cost > 60: continue
        print(f'list: {asset["price"]} | value: {asset["value"]} | total: {asset["stat_total"]} | {name} | {unit_cost}')
        print(json.dumps(asset['stats'], indent=2))

if __name__ == "__main__":
    stats = obtain_stats()
    collection = load_collection()
    set_assets_stats(stats, collection)
    sort_assets(collection)
    display(collection)
    save_collection(collection)
