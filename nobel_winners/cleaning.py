import pandas as pd
import numpy as np
import json
from pymongo import MongoClient

# Create a new DB named 'nobel_prize' and create a new collection titled 'winners'
def create_mongo_database(infile, db_name, collection):
    try:
        client = MongoClient()
        print('... Connected successfully.')
    except:
        print('Cannot connect to MongoDB.')
    db = client[db_name]
    coll = db[collection]
    with open(infile) as f:
        data = json.load(f)
    coll.insert_many(data)
    print('... Imported "%s" into MongoDB with the collection name of "%s".'%(infile, collection))
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

# Create pandas DataFrame from mongoDB collection
def mongo_to_dataframe(db_name, collection, query={}, host='localhost',
                       port=27017, username=None, password=None, no_id=True):
    db = get_mongo_database(db_name, host, port, username, password)
    cursor = db[collection].find(query)
    df = pd.DataFrame(list(cursor))
    print('... Generated pandas DataFrame from "%s" collection in MongoDB.'%(collection))

    if no_id:
        del df['_id']

    return df

# Insert DataFrame into MongoDB
def dataframe_to_mongo(df, db_name, collection, host='localhost',
                       port=27017, username=None, password=None):
    db = get_mongo_database(db_name, host, port, username, password)
    # Use 'records' as orient parameter to generate a list of laureates
    records = json.loads(df.to_json(orient='records', date_format='iso'))
    db[collection].insert_many(records)
    print('... Stored cleaned DataFrame in "%s" collection of "%s" database.'%(collection, db_name))

# Clean data in DataFrame
def clean_data(df):

    print('... Cleaning DataFrame...')

    # Replace '' with NaN value
    df = df.replace('', np.nan)

    # Two DataFrames to return; born_in fields filled with null and those filled with non-null
    df_born_in = df[df.born_in.notnull()]
    df = df[df.born_in.isnull()]
    df = df.drop('born_in', axis=1)

    # Nobel prize started in 1901, so 1809 is impossible
    df.drop(df[df.year == 1809].index, inplace=True)

    # Correct errors manually
    df = df[~(df.name == 'Marie Curie')]
    df = df[~((df.name == 'Sidney Altman') & (df.year == 1990))]
    df.loc[(df.name == 'Alexis Carrel'), 'category'] = 'Physiology or Medicine'

    # Drop duplicates to count each laureate only once
    df = df.reindex(np.random.permutation(df.index))
    df = df.drop_duplicates(['name', 'year'])
    df = df.sort_index()

    # Remove institutional prize winners
    df = df[df.gender.notnull()]

    # Convert the type of date columns into datetime64 data type
    df.date_of_birth = pd.to_datetime(df.date_of_birth)
    df.date_of_death = pd.to_datetime(df.date_of_death, errors='coerce')
    df['award_age'] = df.year - pd.DatetimeIndex(df.date_of_birth).year

    print('... Done with cleaning.')

    return df, df_born_in

if __name__ == '__main__':
    create_mongo_database('nobel_winners_full.json', 'nobel_prize', 'winners')
    df = mongo_to_dataframe('nobel_prize', 'winners')
    df_cleaned, df_born_in = clean_data(df)
    dataframe_to_mongo(df_cleaned, 'nobel_prize', 'winners_cleaned')
    dataframe_to_mongo(df_born_in, 'nobel_prize', 'winners_born_in')
