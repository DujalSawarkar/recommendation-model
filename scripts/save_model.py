import pandas as pd
import numpy as np
import re
import os
import logging
import sys
from pymongo import MongoClient
from datetime import datetime, timedelta, UTC
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import TruncatedSVD
import cloudpickle as pickle
import boto3
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://anushka_ml_team:Vk1818@champhuntindia.nmjhc.mongodb.net/")
# S3_BUCKET = os.getenv("S3_BUCKET", "ml-model-recommendation")
MODEL_KEY = os.getenv("MODEL_KEY", "recommendation_model.pkl")

from app.recommender import PostRecommender

def fetch_data():
    print("fetch_data data..+++.")
    client = MongoClient(MONGO_URI)
    db = client['champhunt_feeds']
    three_months_ago = datetime.now(UTC) - timedelta(days=90)
    posts_data = list(db['feeds'].find({"createdDate": {"$gte": three_months_ago}}))
    db = client['champhunt']
    users_data = list(db['users'].find({}))
    views_data = list(db['userinteractions'].find({}))
    print("By Byefetch_data data..+++.")
    return posts_data, users_data, views_data

def preprocess_data(posts_data, users_data, views_data):
    posts_df = pd.DataFrame(posts_data)
    users_df = pd.DataFrame(users_data)
    views_df = pd.DataFrame(views_data)
    
    posts_df = posts_df[posts_df['postMessage'].notna() & (posts_df['postMessage'].str.strip() != '')]
    posts_df.reset_index(drop=True, inplace=True)
    
    users_df['DOB'] = pd.to_datetime(users_df['DOB'], errors='coerce')
    
    def calculate_age(dob):
        if pd.notna(dob):
            return datetime.now().year - pd.to_datetime(dob).year
        return None
    
    users_df['age'] = users_df['DOB'].apply(calculate_age)
    
    def get_age_group(age):
        if age is None or np.isnan(age):
            return 'unknown'
        elif age < 18:
            return 'teen'
        elif 18 <= age < 30:
            return 'young_adult'
        elif 30 <= age < 50:
            return 'adult'
        else:
            return 'senior'
    
    users_df['age_group'] = users_df['age'].apply(get_age_group)
    
    def is_valid_post(message):
        return bool(re.search(r'[a-zA-Z0-9]', message)) and len(message.strip()) > 5
    
    posts_df = posts_df[posts_df['postMessage'].apply(is_valid_post)]
    posts_df.reset_index(drop=True, inplace=True)
    
    vectorizer = TfidfVectorizer(stop_words='english')
    post_vectors = vectorizer.fit_transform(posts_df['postMessage'].fillna(''))
    
    posts_df['popularity_score'] = (
        0.3 * posts_df['postCommentCount'].fillna(0) +
        0.4 * posts_df['postRunCount'].fillna(0) +
        0.5 * posts_df['impression'].fillna(0)
    )
    
    scaler = MinMaxScaler()
    posts_df['popularity_score'] = scaler.fit_transform(posts_df[['popularity_score']])
    
    views_exploded = views_df.explode('interactions')
    views_exploded = pd.concat([
        views_exploded.drop(columns=['interactions']),
        views_exploded['interactions'].apply(pd.Series)
    ], axis=1)
    
    interaction_matrix = views_exploded.pivot(index='userId', columns='tagId', values='weight').fillna(0)
    
    svd = TruncatedSVD(n_components=50)
    user_factors = svd.fit_transform(interaction_matrix)
    
    return post_vectors, posts_df, interaction_matrix, user_factors, users_df, views_exploded

def save_and_upload_model():
    logger.info("Fetching data...")
    print("Fetching data...")
    posts_data, users_data, views_data = fetch_data()
    logger.info("Preprocessing data...")
    print("Preprocessing data...")
    post_vectors, posts_df, interaction_matrix, user_factors, users_df, views_exploded = preprocess_data(
        posts_data, users_data, views_data
    )
    
    logger.info("Creating model...")
    recommender = PostRecommender(post_vectors, posts_df, interaction_matrix, user_factors, users_df, views_exploded)
    
    os.makedirs("models", exist_ok=True)
    local_path = os.path.join("models", "recommendation_model.pkl")  # Updated to match S3_KEY
    logger.info(f"Saving model to {local_path}...")
    with open(local_path, "wb") as file:
        pickle.dump(recommender, file)
    file_size = os.path.getsize(local_path) / 1e9
    logger.info(f"Model saved locally to {local_path} (size: {file_size:.2f} GB)")
    
    # s3_client = boto3.client(
    #     "s3",
    #     aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    #     aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    #     region_name=os.getenv("AWS_DEFAULT_REGION")
    # )
    # logger.info(f"Uploading model to s3://{S3_BUCKET}/{MODEL_KEY}...")
    # s3_client.upload_file(local_path, S3_BUCKET, MODEL_KEY)
   
    # logger.info(f"Model uploaded to s3://{S3_BUCKET}/{MODEL_KEY}")

if __name__ == "__main__":
    save_and_upload_model()