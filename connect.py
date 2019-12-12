"""
https://api.mongodb.com/python/current/tutorial.html#making-a-connection-with-mongoclient
"""

from pymongo import MongoClient
from settings import MONGODB

client = MongoClient(MONGODB)
databases = client.slp

