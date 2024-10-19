import logging
import os
import shutil
import subprocess
import sys
import time
import requests
from dotenv import load_dotenv

load_dotenv("../../.env")
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
logging.basicConfig(level=logging.INFO, format='molexAI Explore: %(asctime)s - %(levelname)s - %(message)s')

def download_mlxai():
    """Download explore.exe from MolexAI GitHub"""
    if not os.path.exists("explore.exe"):
        explore_url = "https://github.com/molexai/mlx/raw/main/explore.exe"
        local_path = os.path.abspath("explore.exe")
        response = requests.get(explore_url, stream=True)

        if response.status_code == 200:
            with open(local_path, 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)
        else:
            logging.error(f"Failed to download explore.exe: {response.status_code}")

def request_mlxai(model, request):
    """
    Request ML model from MolexAI

    Args:
        model (str): Model name
        request (str): Request to model
    """
    mlxai_path = os.path.abspath("explore.exe")

    if not os.path.exists(mlxai_path):
        logging.warning("MolexAI executable not found. Attempting to download.")
        download_mlxai()

    try:
        start_time = time.time()
        command = [mlxai_path, model, os.getenv("GITHUB_TOKEN"), request]

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error_output = process.communicate()

        if error_output:
            logging.error(f"Error Output: {error_output.decode().strip()}")
            return None

        response = output.decode().strip()
        end_time = time.time()

        rounded_time = round(end_time - start_time, 2)
        logging.info(f"Time taken to respond: {rounded_time} seconds")

        return response

    except Exception as e:
        logging.error(f"An error occurred while requesting the ML model: {e}")
        return None