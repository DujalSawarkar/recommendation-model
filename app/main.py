import os
import sys
# import boto3
import cloudpickle as pickle
from fastapi import FastAPI, Query
import logging
import tempfile
import shutil
from fastapi.middleware.cors import CORSMiddleware

# import scripts.scheduler
# from scripts.scheduler import run_save_and_load_model

from dotenv import load_dotenv


# Add parent directory to sys.path for local execution
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now the imports should work
from app.recommender import PostRecommender
from app.data_processing import fetch_ads
from app.utils import insert_ads

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify a list of allowed frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://anushka_ml_team:Vk1818@champhuntindia.nmjhc.mongodb.net/")
# S3_BUCKET = os.getenv("S3_BUCKET", "ml-model-recommendation")
MODEL_KEY = os.getenv("MODEL_KEY", "recommendation_model.pkl")

# run_save_and_load_model()

def download_model_from_s3():
    # s3_client = boto3.client(
    #     "s3",
    #     aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    #     aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    #     region_name=os.getenv("AWS_DEFAULT_REGION")
    # )
    # Specify a custom temp directory
    # temp_dir = os.getenv("TEMP_DIR", "D:\\temp")
    cwd = os.getcwd()
    local_temp_folder = "TEMP_DIR"
    local_model_folder = "models"
    model_file_name = "recommendation_model.pkl"
    relative_TEMP_DIR_Path = os.path.join(cwd,local_temp_folder)
    model_local_path = os.path.join(cwd,local_model_folder, model_file_name) 
    os.makedirs(relative_TEMP_DIR_Path, exist_ok=True)
    # Create a temporary file path without opening it initially
    # with tempfile.NamedTemporaryFile(delete=False, suffix=".pkl", dir=relative_TEMP_DIR_Path) as tmp_file:
    #     local_path = tmp_file.name
    # Download directly to the temporary file
    # logger.info(f"Downloading model from s3://{S3_BUCKET}/{MODEL_KEY} to {local_path}")
    # s3_client.download_file(S3_BUCKET, MODEL_KEY, local_path)
    model_temp_path = os.path.join(relative_TEMP_DIR_Path, model_file_name)
    shutil.copy2(model_local_path,model_temp_path)
    print(model_temp_path)
    return model_temp_path

def load_model():
    model_path = download_model_from_s3()
    logger.info(f"Loading model from {model_path}")
    try:
        with open(model_path, "rb") as file:
            recommender = pickle.load(file)
        logger.info("Model loaded successfully")
        os.unlink(model_path)  # Clean up
        return recommender
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        if os.path.exists(model_path):
            os.unlink(model_path)  # Ensure cleanup on error
        raise

recommender = load_model()

@app.get("/")
async def home():
    return {"message": "Recommendation API is running!"}

@app.get("/recommend")
async def get_recommendations(user_id: str = Query(None), top_n: int = 10, num_ads: int = 3):
    try:
        if user_id:
            recommendations = recommender.recommend_posts(user_id, top_n)
        else:
            recommendations = recommender.recommend_global_posts(top_n)

        recommendations["_id"] = recommendations["_id"].astype(str)
        
        ads_df = fetch_ads(MONGO_URI)
        result = insert_ads(recommendations, ads_df, num_ads)
        
        return {"recommendations": result}
    except Exception as e:
        logger.error(f"Error in get_recommendations: {e}")
        return {"error": str(e)}