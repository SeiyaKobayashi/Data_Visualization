import pandas as pd
import json
from pymongo import MongoClient

# Create a new DB named 'nobel_prize' and create a new collection titled 'winners'
def create_mongo_database():
    try:
        client = MongoClient()
        print('Connected successfully.')
    except:
        print('Cannot connect to MongoDB.')
    db = client['nobel_prize']
    coll = db['winners']
    with open('nobel_winners_full.json') as f:
        data = json.load(f)
    coll.insert_many(data)
    client.close()

# Get MongoDB
def get_mongo_database(db_name, host='localhost', port=27017,
                       username=None, password=None):
    if username and password:
        mongo_uri = 'mongodb://%s:%s@%s%s'%(username, password, host, db_name)
        conn = MongoClient(mongo_uri)
    else:
        conn = MongoClient(host, port)

    return conn[db_name]

def mongo_to_dataframe(db_name, collection, query={}, host='localhost',
                       port=27017, username=None, password=None, no_id=True):
    db = get_mongo_database(db_name, host, port, username, password)
    cursor = db[collection].find(query)
    df = pd.DataFrame(list(cursor))

    if no_id:
        del df['_id']

    return df

if __name__ == '__main__':
    create_mongo_database()
    df = mongo_to_dataframe('nobel_prize', 'winners')
    print(df.info())
