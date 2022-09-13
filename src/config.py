import os


# Common 
DEBUG_MODE = True


# Database
MONGO_URI = f'mongodb+srv://androo:{os.environ["MONGO_PASS"]}@rarity.p1eftav.mongodb.net/?retryWrites=true&w=majority'
DB_NAME = 'rarity'


# Server
HOST = '0.0.0.0'
PORT = 8000