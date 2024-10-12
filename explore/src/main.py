import os
import shutil
import subprocess
import sys

import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def download_mlxai():
    if not os.path.exists("codepilot.exe"):
        explore_url = "https://github.com/molexai/mlx/raw/main/explore.exe"
        local_path = os.path.abspath("explore.exe")
        response = requests.get(explore_url, stream=True)

        if response.status_code == 200:
            with open(local_path, 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)
        else:
            print(f"Failed to download explore.exe: {response.status_code}")

def request_mlxai(model, request):
    mlxai_path = os.path.abspath("explore.exe")

    if not os.path.exists(mlxai_path):
        download_mlxai()

    try:
        process = subprocess.Popen(
            [mlxai_path,
             model,
             os.getenv("GITHUB_TOKEN"),
             request],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        output, error_output = process.communicate()

        if error_output:
            print(f"Error Output: {error_output.decode().strip()}")

        return output.decode().strip()
    except Exception as e:
        print(e)
        return ""
