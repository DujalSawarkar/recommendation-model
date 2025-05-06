# from apscheduler.schedulers.blocking import BlockingScheduler
# import subprocess
# from datetime import datetime
# import os

# def run_save_and_load_model():
#     base_dir = os.path.dirname(__file__)
#     save_model_path = os.path.join(base_dir, "save_model.py")
#     test_load_path = os.path.join(base_dir, "test_load.py")
    
#     print(f"[{datetime.now()}] Running save_model.py...")
#     subprocess.run([r"E:\deploy_1\venv310\Scripts\python.exe", save_model_path])

#     print(f"[{datetime.now()}] Running test_load.py...")
#     subprocess.run([r"E:\deploy_1\venv310\Scripts\python.exe", test_load_path])
    
# scheduler = BlockingScheduler()
# scheduler.add_job(run_save_and_load_model, 'interval', minutes=30)

# print("Scheduler started. Running every 30 minutes..." , datetime.now())
# scheduler.start()

# scheduler.py
import os
import sys
import logging
import subprocess
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_save_and_test():
    """Run save_model.py then test_load.py with the current Python interpreter."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    python_exe = sys.executable

    save_script = os.path.join(base_dir, "save_model.py")
    test_script = os.path.join(base_dir, "test_load.py")

    logger.info(f"[{datetime.now()}] Running {save_script} with {python_exe}...")
    subprocess.run([python_exe, save_script], check=True)

    logger.info(f"[{datetime.now()}] Running {test_script} with {python_exe}...")
    subprocess.run([python_exe, test_script], check=True)

if __name__ == "__main__":
    scheduler = BlockingScheduler()
    # run every 30 minutes, starting immediately
    scheduler.add_job(
        run_save_and_test,
        trigger="interval",
        minutes=30,
        next_run_time=datetime.now(),
        misfire_grace_time=300  # optional: allow up to 5min grace
    )
    logger.info(f"Scheduler started. Running every 30 minutes... {datetime.now()}")
    scheduler.start()
