import logging
import os
import shutil
import subprocess
import sys
import time

import requests

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
            print(f"Failed to download explore.exe: {response.status_code}")

def request_mlxai(model, request, image_path=None):
    """
    Request ML model from MolexAI

    Args:
        model (str): Model name
        request (str): Request to model
        image_path (str): Path to image file
    """
    mlxai_path = os.path.abspath("explore.exe")

    if not os.path.exists(mlxai_path):
        logging.warning("MolexAI executable not found. Attempting to download.")
        download_mlxai()

    try:
        command = [mlxai_path, model, os.getenv("GITHUB_TOKEN"), request]

        if image_path:
            command.append(image_path)

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error_output = process.communicate()

        if error_output:
            logging.error(f"Error Output: {error_output.decode().strip()}")

        response = output.decode().strip()
        logging.info("Response received from ML model.")

        end_time = time.time()
        rounded_time = round(end_time - process.start_time, 2)
        logging.info(f"Time taken to respond: {rounded_time} seconds")

        return response

    except Exception as e:
        logging.error(f"An error occurred while requesting the ML model: {e}")
        return None

print(request_mlxai("gpt-4o-mini", "QUERY_OF_IMAGE: what is google?", "screenshots/screenshot-c28e992c-cfb9-48a0-8b01-faceaaa309ec.png"))