import cloudpickle as pickle
import logging
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.recommender import PostRecommender

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to the saved model (absolute path for reliability)
model_path = os.path.join(os.path.dirname(__file__), "..", "models", "recommendation_model.pkl")

try:
    # Verify file exists
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}")

    # Load the model
    with open(model_path, "rb") as file:
        recommender = pickle.load(file)
    logger.info("Model loaded successfully")

    # Verify the class and module
    logger.info(f"Model class: {recommender.__class__.__name__}")
    logger.info(f"Model module: {recommender.__class__.__module__}")

    # Optional: Test a method to ensure functionality
    if hasattr(recommender, "recommend_global_posts"):
        sample_recommendation = recommender.recommend_global_posts(top_n=2)
        logger.info(f"Sample recommendation: {sample_recommendation}")
    else:
        logger.warning("recommend_global_posts method not found")

except Exception as e:
    logger.error(f"Failed to load model: {e}")
    raise