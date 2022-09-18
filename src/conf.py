import os


# Common 
DEBUG_MODE = True

# Server
HOST = '0.0.0.0'
PORT = 80

# Graphql
ENDPOINT = 'https://graphql-api.mainnet.dandelion.link'

# Database
MONGO_URI = f'mongodb+srv://androo:{os.environ["MONGO_PASS"]}@rarity.p1eftav.mongodb.net/?retryWrites=true&w=majority'
DB_NAME = 'rarity'
DB_ENDPOINT = f'http://{HOST}:{PORT}'
