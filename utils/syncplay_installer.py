import os
import requests
import zipfile
from tqdm import tqdm

def install_syncplay_portable():
    url = "https://github.com/Syncplay/syncplay/releases/download/v1.7.4/Syncplay_1.7.4_Portable.zip"
    target_folder = "syncplay"
    os.makedirs(target_folder, exist_ok=True)
    zip_path = os.path.join(target_folder, "Syncplay_Portable.zip")

    # Download the zip file with progress bar
    print("Downloading Syncplay portable zip...")
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024  # 1 KB

    with open(zip_path, "wb") as f, tqdm(
        total=total_size,
        unit='B',
        unit_scale=True,
        desc="Downloading",
        bar_format='{l_bar}{bar:40}{r_bar}'
    ) as progress_bar:
        for chunk in response.iter_content(block_size):
            f.write(chunk)
            progress_bar.update(len(chunk))
        progress_bar.set_description("Download completed")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        file_list = zip_ref.infolist()
        with tqdm(
            total=len(file_list),
            unit='file',
            desc="Extracting",
            bar_format='{l_bar}{bar:40}{r_bar}'
        ) as progress_bar:
            for file in file_list:
                zip_ref.extract(file, target_folder)
                progress_bar.update(1)
            progress_bar.set_description("Installation completed")

    # Optionally, remove the zip file after extraction
    os.remove(zip_path)
    print("Syncplay installed successfully\n")