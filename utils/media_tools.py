import os
import time
import re
import requests
from urllib.parse import urljoin
import glob
import subprocess
from utils.inits import LOG_FILE

def getVideoLinks(file_url, timeout=5, poll_interval=2):
    video_extensions = (
        "3g2", "3gp", "apng", "avc", "avi", "avs", "avs2", "c2", "cdxl", "cgi",
        "cif", "dif", "dv", "f4v", "flv", "gif", "h261", "h263", "h264", "h265",
        "h26l", "hevc", "idf", "ism", "isma", "ismv", "j2k", "m4a", "m4b", "m4v",
        "mj2", "mjpeg", "mjpg", "mk3d", "mka", "mks", "mkv", "mov", "mp4", "mpo",
        "mvi", "obu", "ogg", "psp", "qcif", "rgb", "v210", "vc1", "xl", "yuv", "yuv10"
    )

    if not file_url or not file_url.startswith("http://"):
        print("Invalid or missing file URL.")
        return []
    
    # Extract root directory URL (up to the hash)
    url_parts = file_url.rstrip('/').split('/')
    hash_index = next((i for i, part in enumerate(url_parts) if len(part) == 40 and re.match(r'[0-9a-f]{40}', part)), -1)
    if hash_index == -1 or hash_index + 1 >= len(url_parts):
        print("Invalid URL format: Could not find hash or directory.")
        return []
    
    root_url = '/'.join(url_parts[:hash_index + 1]) + '/'
    
    # Poll the root directory until listing is available
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(root_url, timeout=5)
            response.raise_for_status()
            
            # Find all links using regex
            links = []
            # Create regex pattern for video files
            ext_pattern = '|'.join(re.escape(ext) for ext in video_extensions)
            pattern = rf'href="([^"]*\.(?:{ext_pattern}))"'
            
            for match in re.finditer(pattern, response.text, re.IGNORECASE):
                href = match.group(1)
                # Skip parent directory
                if href == '../':
                    continue
                # Encode only spaces to match WebTorrent's URL format
                href_encoded = href.replace(' ', '%20')
                # Use urljoin to properly construct the URL
                full_url = urljoin(root_url, href_encoded)
                full_url = full_url.replace('\\', '/')
                links.append(full_url)
            
            # Remove duplicates and sort
            links = list(dict.fromkeys(links))
            links.sort()
            
            if not links:
                print("No video files found yet, retrying...")
                time.sleep(poll_interval)
                continue
 
            return links
        
        except requests.RequestException as e:
            print(f"Server not ready ({e}), retrying in {poll_interval} seconds...")
            time.sleep(poll_interval)
    
    print(f"Failed to access {root_url} within {timeout} seconds.")
    return []

def getStreamableLink(proc,MAGNET=None):
    # Regex to capture HTTP link
    http_pattern = re.compile(r"http://[^\s]+")

    link = None

    # Read stdout line by line
    for line in proc.stdout:
        line = line.strip()
        match = http_pattern.search(line)
        if match:
            link = match.group()
            break
    
    return link

def retrieveStreamLinks(number=None):
    number = int(number)
    streamLinks = []

    with open(LOG_FILE, "r") as f:
        count = 0
        lines = f.read().split('\n')
        for line in lines:
            if line.startswith("magnet:"):
                count += 1
            if count == number and line.startswith("http://"):
                line.strip()
                streamLinks.append(line)
        return streamLinks

def retrieveMagnetLink(number=None):
    number = int(number)
    with open(LOG_FILE, "r") as f:
        count = 0
        lines = f.read().split('\n')
        for line in lines:
            if line.startswith("magnet:"):
                count += 1
            if count == number:
                line = line.strip()
                return line
        return None
    
def getSortedLogFileEntries():
    cache_dir = "cached_files"
    if not os.path.exists(cache_dir):
        return None
    
    # Get all files and directories in cached_files, excluding logs.txt
    entries = [entry for entry in glob.glob(os.path.join(cache_dir, "*")) 
              if os.path.basename(entry) != "logs.txt"]
    
    # Sort entries by modification time (oldest first)
    entries.sort(key=lambda x: os.path.getmtime(x))
    
    # Return just the basenames of the entries
    return [os.path.basename(entry) for entry in entries]

def add(MAGNET=None):
    if not MAGNET:
        print("No magnet link provided.")
        return
    with open(LOG_FILE, "r") as f:
        existing_log = f.read()
        if MAGNET in existing_log:
            print("movie is already added")
            return

    print("Magnet is adding...")
    # Start WebTorrent in Python (unbuffered)
    proc = subprocess.Popen(
        f'webtorrent "{MAGNET}" --keep-seeding',
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        universal_newlines=True,
        shell=True,
        cwd="cached_files"
    )
    from utils.media_tools import getStreamableLink,getVideoLinks
    link = getStreamableLink(proc=proc,MAGNET=MAGNET)

    streamLinks = getVideoLinks(file_url=link)
    
    proc.terminate()
    time.sleep(0.5)  # small delay to ensure termination
    # Save the HTTP link to file l
    if streamLinks:
        with open(LOG_FILE, "a") as f:
            f.write(MAGNET + "\n"  )
            for link in streamLinks:
                f.write(link + "\n")
            f.write("\n")
    else:
        print("something went wrong, no link found")
        return
    print(f"Magnet added successfully.")