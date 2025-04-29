from pymongo import MongoClient
import pandas as pd

def fetch_ads(mongo_uri):
    client = MongoClient(mongo_uri)
    db = client['champhunt']
    ads_collection = db['ads']
    ads_data = list(ads_collection.find({}))
    ads_df = pd.DataFrame(ads_data)
    
    if "_id" in ads_df.columns:
        ads_df["id"] = ads_df["_id"].astype(str)
        ads_df = ads_df[["id", "title"]]
    
    return ads_df