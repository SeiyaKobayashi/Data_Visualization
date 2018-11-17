from pymongo import MongoClient

client = MongoClient()
client.drop_database('nobel_prize')
