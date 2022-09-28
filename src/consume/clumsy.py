from bs4 import BeautifulSoup
import aiohttp
import asyncio
import time
import re

from .services import Project, Collection

def load_collection(policy):
    project = Project("Clumsy Studios")
    project.get_or_create()

    collection = Collection("Clumsy Ghosts", policy, project.id)
    collection.load_collection()    
    collection.load_assets()
    collection.fetch_assets()
    return collection


async def update_all_assets(n, collection, regex):
    conn = aiohttp.TCPConnector(limit=0, ttl_dns_cache=300)
    session = aiohttp.ClientSession(connector=conn)
    semaphore = asyncio.Semaphore(n)

    async def set_hidden(metadata, url):
        async with semaphore:
            values = None
            while not values:
                async with session.get(url, ssl=False) as resp:
                    if not resp.ok: 
                        await asyncio.sleep(10)
                        continue
                    html = await resp.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    values = re.findall(regex, soup.script.string)
                    print(values)
                    metadata['hidden'] += values

    tasks = []
    for asset in collection.assets:
        metadata = asset['metadata']
        if metadata.get('hidden'): continue
        metadata['hidden'] = []
        for file in metadata['files']:
            src = file['src']        
            ipfs = re.search('Qm[1-9a-zA-Z]{44}', src).group(0)
            url = f"https://ipfs.io/ipfs/{ipfs}"
            task = asyncio.ensure_future(set_hidden(metadata, url))
            tasks.append(task)

    await asyncio.gather(*tasks)
    await session.close()
    conn.close()

def update_clumsy_hidden(policy):
    collection = load_collection(policy)

    PARALLEL_REQUESTS = 120
    start = time.time()
    ghost_regex = "(?<=classList.add\(').+?(?='\))"
    asyncio.run(update_all_assets(PARALLEL_REQUESTS, collection, ghost_regex))
    end = time.time()
    print(f'{end - start} seconds elapsed.')

    collection.set_properties()
    collection.set_facets()
    collection.update()
    collection.calc_string_stat_rarity()
    collection.update_assets()

async def fetch_all_scripts(n):
    results = {}
    conn = aiohttp.TCPConnector(limit=0, ttl_dns_cache=300)
    session = aiohttp.ClientSession(connector=conn)
    semaphore = asyncio.Semaphore(n)

    async def set_script(serial, url):
        async with semaphore:
            values = None
            while not values:
                async with session.get(url, ssl=False) as resp:
                    if not resp.ok: 
                        await asyncio.sleep(10)
                        continue
                    print(serial)
                    html = await resp.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    values = soup.script.string
                    results[serial] = values

    tasks = []
    for serial in range(1, 10001):
        url = f"https://assets.clumsylabs.io/land/ipfs/ClumsyValleyLandPlot{serial}.svg"
        task = asyncio.ensure_future(set_script(serial, url))
        tasks.append(task)

    await asyncio.gather(*tasks)
    await session.close()
    conn.close()
    return results