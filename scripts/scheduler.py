from apscheduler.schedulers.blocking import BlockingScheduler
import subprocess
from datetime import datetime
import os

def run_save_and_load_model():
    base_dir = os.path.dirname(__file__)
    save_model_path = os.path.join(base_dir, "save_model.py")
    test_load_path = os.path.join(base_dir, "test_load.py")

    print(f"[{datetime.now()}] Running save_model.py...")
    subprocess.run(["python", save_model_path])

    print(f"[{datetime.now()}] Running test_load.py...")
    subprocess.run(["python", test_load_path])
    
scheduler = BlockingScheduler()
scheduler.add_job(run_save_and_load_model, 'interval', minutes=30)

print("Scheduler started. Running every 30 minutes...")
scheduler.start()