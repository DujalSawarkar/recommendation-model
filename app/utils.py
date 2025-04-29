import pandas as pd
import random

def insert_ads(recommendations, ads_df, num_ads):
    recommendations_list = recommendations.to_dict(orient="records")
    
    if ads_df.empty or num_ads <= 0:
        return recommendations_list
    
    ads_list = ads_df.sample(n=min(num_ads, len(ads_df))).to_dict(orient="records")
    combined_list = recommendations_list + [{"type": "ad", **ad} for ad in ads_list]
    
    random.shuffle(combined_list)
    return combined_list