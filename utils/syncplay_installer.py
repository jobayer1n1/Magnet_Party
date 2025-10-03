import os
import zipfile
import requests

def install_syncplay_portable():
    url = "https://github.com/Syncplay/syncplay/releases/download/v1.7.4/Syncplay_1.7.4_Portable.zip"
    target_folder = "syncplay"
    os.makedirs(target_folder, exist_ok=True)
    zip_path = os.path.join(target_folder, "Syncplay_Portable.zip")
    
    # Download the zip file
    print("Downloading Syncplay portable zip...")
    response = requests.get(url)
    with open(zip_path, "wb") as f:
        f.write(response.content)
    print("Download complete.")
    
    # Extract the zip file
    print("Extracting Syncplay...")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(target_folder)
    print("Syncplay extracted to:", target_folder)
    
    # Optionally, remove the zip file after extraction
    os.remove(zip_path)
    print("Syncplay installed successfully\n")
