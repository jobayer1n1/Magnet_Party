import os
import sys
import subprocess
import threading
import requests
import zipfile
import time
import re
import shutil
from urllib.parse import urljoin, unquote
import stat
from urllib.parse import quote, unquote, urljoin
import pathlib
import argparse
import glob
import tempfile
import platform
import ctypes
from ctypes import wintypes

LOG_FILE = "cached_files/logs.txt"
PLAYER_PATH = ""
PLAYER_NAME = ""

BASE = "https://yts.mx/api/v2/"

def search_yts(query, limit=5):
    url = f"{BASE}list_movies.json"
    params = {"query_term": query, "limit": limit}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    
    if data["status"] != "ok" or not data["data"]["movie_count"]:
        return []
    
    results = []
    for movie in data["data"]["movies"]:
        torrents = []
        for t in movie.get("torrents", []):
            torrents.append({
                "quality": t["quality"],
                "type": t["type"],
                "size": t["size"],
                "seeds": t["seeds"],
                "peers": t["peers"],
                "hash": t["hash"],
                "movie_title": movie["title_long"]
            })
        results.append({
            "title": movie["title_long"],
            "year": movie["year"],
            "rating": movie["rating"],
            "torrents": torrents
        })
    return results

def make_magnet(hashcode, title):
    return (
        f"magnet:?xt=urn:btih:{hashcode}"
        f"&dn={title.replace(' ', '+')}"
        f"&tr=udp://tracker.openbittorrent.com:80/announce"
    )

def search_movie():
    print("--- YTS ---")
    print("Enter a movie name : ")
    query = input("main->movie search > ").strip()
    movies = search_yts(query)
    
    if not movies:
        print("No results found.")
    else:
        # Show movies
        for i, m in enumerate(movies, start=1):
            print(f"{i}. {m['title']} ({m['year']}) ⭐ {m['rating']}")
        
        while True:
            print("\nSelect a movie or b to back : ")
            choice = input("main->movie search > ")
            if choice =="b":
                return
            if choice.isdigit() and int(choice)<=len(movies):
                choice = int(choice) - 1
                movie = movies[choice]
                break
            else:
                print("invalid input")
        
        # Show torrents
        for j, t in enumerate(movie['torrents'], start=1):
            print(f"{j}. {t['quality']} {t['type']} | {t['size']} | S:{t['seeds']} P:{t['peers']}")
        

        while True:
            print("\nSelect resulation or b to back : ")
            t_choice = input("main->movie search > ")
            if t_choice =="b":
                return
            if t_choice.isdigit() and int(t_choice) <= len(movie['torrents']):
                t_choice = int(t_choice) - 1
                torrent = movie['torrents'][t_choice]
                break
            else : 
                print("invalid input")
        
        # Only now show magnet
        magnet = make_magnet(torrent["hash"], torrent["movie_title"])
        
        add(magnet)


def run_as_admin_and_wait(command):
    """
    Run a command in a new elevated terminal window (Admin privileges)
    and wait until it finishes.
    """
    SEE_MASK_NOCLOSEPROCESS = 0x00000040

    class SHELLEXECUTEINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("fMask", wintypes.ULONG),
            ("hwnd", wintypes.HWND),
            ("lpVerb", wintypes.LPCWSTR),
            ("lpFile", wintypes.LPCWSTR),
            ("lpParameters", wintypes.LPCWSTR),
            ("lpDirectory", wintypes.LPCWSTR),
            ("nShow", ctypes.c_int),
            ("hInstApp", wintypes.HINSTANCE),
            ("lpIDList", wintypes.LPVOID),
            ("lpClass", wintypes.LPCWSTR),
            ("hkeyClass", wintypes.HKEY),
            ("dwHotKey", wintypes.DWORD),
            ("hIcon", wintypes.HANDLE),
            ("hProcess", wintypes.HANDLE),
        ]

    shell32 = ctypes.windll.shell32
    sei = SHELLEXECUTEINFO()
    sei.cbSize = ctypes.sizeof(sei)
    sei.fMask = SEE_MASK_NOCLOSEPROCESS
    sei.hwnd = None
    sei.lpVerb = "runas"            # force admin
    sei.lpFile = "cmd.exe"
    sei.lpParameters = f"/c {command}"
    sei.lpDirectory = None
    sei.nShow = 1  # SW_SHOWNORMAL

    if not shell32.ShellExecuteExW(ctypes.byref(sei)):
        raise ctypes.WinError()

    # Wait until process finishes
    kernel32 = ctypes.windll.kernel32
    kernel32.WaitForSingleObject(sei.hProcess, -1)

    exit_code = wintypes.DWORD()
    kernel32.GetExitCodeProcess(sei.hProcess, ctypes.byref(exit_code))
    kernel32.CloseHandle(sei.hProcess)

    return exit_code.value == 0


def install_nodejs():
    """Download Node.js MSI and run installer in elevated terminal, wait for it to finish."""
    arch = "x64" if platform.architecture()[0] == "64bit" else "x86"
    node_version = "18.20.4"
    node_url = f"https://nodejs.org/dist/v{node_version}/node-v{node_version}-{arch}.msi"

    temp_dir = tempfile.gettempdir()
    installer_path = os.path.join(temp_dir, "node-installer.msi")

    print("⬇ Downloading Node.js installer...")
    response = requests.get(node_url, stream=True, timeout=60)
    if response.status_code == 200:
        with open(installer_path, "wb") as f:
            shutil.copyfileobj(response.raw, f)
        print(f"✔ Node.js installer saved to {installer_path}")
    else:
        raise RuntimeError(f"Failed to download Node.js installer (HTTP {response.status_code})")

    cmd = f'msiexec /i "{installer_path}" /quiet /norestart'
    return run_as_admin_and_wait(cmd)


def install_webtorrent():
    """Install webtorrent-cli globally in elevated terminal, wait for it to finish."""
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    cmd = f'{npm_cmd} install -g webtorrent-cli'
    return run_as_admin_and_wait(cmd)


def install_nodejs_and_webtorrent():
    """Ensure Node.js and webtorrent-cli are installed in sequence."""

    def run_command(cmd):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True,shell=True)
            return True, result.stdout.strip()
        except Exception:
            return False, None

    def check_node():
        ok, out = run_command(["node", "--version"])
        if ok:
            return True
        else:
            print("✘ Node.js not found.")
            return False


    def check_webtorrent():
        ok, out = run_command(["webtorrent", "--version"])
        if ok:
            return True
        else:
            print("✘ webtorrent-cli not found.")
            return False


    node_ok = check_node()
    webtorrent_ok = check_webtorrent()

    if node_ok and webtorrent_ok:
        return True

    if not node_ok:
        print("Node.js missing → launching installer (waiting)...")
        if not install_nodejs():
            print("✘ Node.js installation failed.")
            return False
        print("✔ Node.js installed successfully.")

    if not webtorrent_ok:
        print("⚙ webtorrent-cli missing → launching installer (waiting)...")
        if not install_webtorrent():
            print("✘ webtorrent-cli installation failed.")
            return False
        print("✔ webtorrent-cli installed successfully.")

    print("Setup complete: Node.js and webtorrent-cli are installed.")
    return True

def add_to_path_temp(directory_to_add):
    """
    Adds a directory to the PATH environment variable for the current process.
    """
    current_path = os.environ.get('PATH', '')
    if directory_to_add not in current_path:
        os.environ['PATH'] = f"{directory_to_add};{current_path}"
        return
    else:
        return


def read_file_safely(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

def load_player():
    info = read_file_safely("player.txt")
    if(info==None):
        print("Player isn't set yet")
        playerSet()
    info = read_file_safely("player.txt")
    lines = info.split("\n")
    global PLAYER_NAME
    PLAYER_NAME = lines[0]
    global PLAYER_PATH 
    PLAYER_PATH =  lines[1]



def handle_remove_readonly(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def cache_clear():
    if os.path.exists("cached_files"):
        try:
            shutil.rmtree("cached_files", onerror=handle_remove_readonly)
        except PermissionError:
            # Kill processes locking the folder (e.g., VLC, WebTorrent)
            subprocess.run('taskkill /F /IM vlc.exe', shell=True)
            subprocess.run('taskkill /F /IM node.exe', shell=True)
            shutil.rmtree("cached_files", onerror=handle_remove_readonly)

    initCacheFiles()
    initLog()

def initLog():
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w") as f:
                f.write("")

def initPlaylist():
    if not os.path.exists("cached_files/playlists"):
        os.makedirs("cached_files/playlists")


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

def stream(number):
    number = int(number)
    magnetLink = retrieveMagnetLink(number=number)
    if not magnetLink:
        print("Invalid selection or missing links.")
        return
    os.system(f'start cmd /k webtorrent "{magnetLink}" --keep-seeding --out cached_files --playlist --{PLAYER_NAME} ')

            
            

def playConsole():
    sorted_entries = getSortedLogFileEntries()
    if not sorted_entries:
        print("No torrent found.")
        print("Add a torrent first.")
        return
    print("Added torrent(s) : ")
    for i, d in enumerate(sorted_entries, start=1):
        entry_type = "[DIR]" if os.path.isdir(os.path.join("cached_files", d)) else "[FILE]"
        print(f'{i}- {d} {entry_type}')
    
    print("Enter the respective number to stream or b to back:")
    while True:
        print("main->play > ", end="")
        command = input()
        command = command.strip()
        if command == "b":
            return
        elif not command.isdigit() or int(command) < 1 or int(command) > len(sorted_entries):
            print("Invalid input. Please enter a valid number.")
        elif command.isdigit():
            break
    line = int(command)
    stream(number=line)

    

def add(MAGNET=None):
    if not MAGNET:
        print("No magnet link provided.")
        return
    with open(LOG_FILE, "r") as f:
        existing_log = f.read()
        if MAGNET in existing_log:
            print("movie is already added")
            return

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
    print(f"Torrent added successfully.")





def initCacheFiles():
    if not os.path.exists('cached_files'):
        os.makedirs('cached_files')



def clearScreen():
    os.system('cls' if os.name == 'nt' else 'clear')


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


def find_webtorrent_media_players():
    """
    Check for WebTorrent-supported media players available on a Windows PC.
    Returns a dictionary with player names as keys and their executable paths as values.
    """
    # List of WebTorrent-supported software media players and their typical Windows executable names
    media_players = {
        "MPlayer": "mplayer.exe",
        "MPV": "mpv.exe",
        "VLC": "vlc.exe",
        "IINA": "iina.exe",
        "SMPlayer": "smplayer.exe",
        "XBMC": "kodi.exe"
    }

    # Common installation directories on Windows
    common_paths = [
        pathlib.Path(os.environ.get("ProgramFiles", "C:\\Program Files")),
        pathlib.Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")),
        pathlib.Path(os.environ.get("LocalAppData", os.path.expanduser("~\\AppData\\Local"))) / "Programs",
    ]

    # Dictionary to store available media players and their paths
    available_players = {}

    for player, executable in media_players.items():
        found_path = None
        
        # Check if executable exists in PATH
        try:
            result = subprocess.run(["where", executable], capture_output=True, text=True, check=True)
            if result.stdout.strip():
                found_path = result.stdout.split('\n')[0].strip()
                available_players[player] = found_path
                continue
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Check common installation directories if not found in PATH
        if player not in available_players:
            for base_path in common_paths:
                try:
                    for path in base_path.rglob(executable):
                        if path.is_file():
                            found_path = str(path.resolve())
                            available_players[player] = found_path
                            break
                    if found_path:
                        break
                except (PermissionError, OSError):
                    continue

    return available_players


def playerSet():

    print("Searching for WebTorrent-supported media players...")
    available_players = find_webtorrent_media_players()
    
    if not available_players:
        print("No WebTorrent-supported media players found on this Windows PC.")
        print("Network-based devices (Apple TV, Chromecast, DLNA) require network discovery.")
        return
    
    print("\nAvailable WebTorrent-supported media players:")
    players_list = list(available_players.keys())
    
    for i, player in enumerate(players_list, 1):
        print(f"{i}. {player} - {available_players[player]}")
    
    
    while True:
        try:

            if PLAYER_NAME !="":
                print("\nChoose a player or b to back : ")
            else:
                print("\nChoose a player : ", end="")
                choice = input().strip()
            
            if choice =="b" and PLAYER_NAME != "":
                return
            
            if choice == str(len(players_list) + 1):
                print("Operation cancelled.")
                return
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(players_list):
                selected_player = players_list[choice_num - 1]
                selected_path = available_players[selected_player]
                
                print(f"\nYou selected: {selected_player}")
                print(f"Executable path: {selected_path}")
                
                confirm = input("Confirm? y or yes : ").strip().lower()
                if confirm in ['y', 'yes']:
                    print(f"\nPlayer Selected Successfully")
                    with open("player.txt","w") as file:
                            player_name = str(selected_player).lower()
                            path = str(selected_path).lower()
                            file.write(player_name+"\n"+path)
                else:
                    print("Operation cancelled.")
                return
            else:
                print(f"Please enter a number between 1 and {len(players_list) + 1}")
                
        except ValueError:
            print("Please enter a valid number.")
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            return

def streamWithFriend():

    HOST = "syncplay.pl:8999"
    NAME = ""  # Default name
    ROOM = ""  # Default room
    SYNCPLAY_PATH = os.path.join("syncplay", "syncplay.exe")
    PLAYLIST_PATH = os.path.abspath(os.path.join("cached_files", "syncplay_playlist.txt"))  # Playlist file for Syncplay

    def create_playlist_file(stream_links, playlist_path=PLAYLIST_PATH):
        """Create a playlist file with one stream URL per line."""
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(playlist_path), exist_ok=True)
            with open(playlist_path, 'w', encoding='utf-8') as f:
                for link in stream_links:
                    f.write(f"{link}\n")  # One URL per line
            print(f"Created playlist file: {playlist_path}")
            time.sleep(1)  # Ensure file is fully written
            if not os.path.exists(playlist_path):
                print(f"Error: Playlist file {playlist_path} was not created.")
                return None
            # Verify file accessibility
            with open(playlist_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content:
                    print(f"Error: Playlist file {playlist_path} is empty.")
                    return None
            print(f"Playlist file content verified: {content[:100]}...")  # Log first 100 chars
            return playlist_path
        except Exception as e:
            print(f"Error creating or verifying playlist file: {e}")
            return None

    def playwithSyncPlay(playlist_path, name, room, host):
        # Set up command line argument parser
        parser = argparse.ArgumentParser(description='Run Syncplay with specified room and name')
        parser.add_argument('-n', '--name', type=str, default=name, help=f'Your display name (default: {name})')
        parser.add_argument('-r', '--room', type=str, default=room, help=f'Room to join (default: {room})')
        parser.add_argument('--host', type=str, default=host, help=f'Syncplay server host (default: {host})')
        
        args = parser.parse_args()

        # Load player path
        load_player()
        
        # Verify paths
        if not os.path.exists(SYNCPLAY_PATH):
            print(f"Error: {SYNCPLAY_PATH} not found.")
            exit(1)
        if not os.path.exists(PLAYER_PATH):
            print(f"Error: {PLAYER_PATH} not found.")
            exit(1)
        
        # Verify playlist file exists
        if not os.path.exists(playlist_path):
            print(f"Error: Playlist file {playlist_path} not found.")
            print(f"Ensure the directory containing {playlist_path} is added to Syncplay's media directories.")
            print(f"In Syncplay, go to File -> Set Media Directories and add {os.path.dirname(playlist_path)}")
            exit(1)

        # Construct Syncplay command with --load-playlist-from-file
        command = [
            SYNCPLAY_PATH,
            "-a", args.host,                           # --host
            "-n", args.name,                           # --name  
            "-r", args.room,                           # --room
            "--player-path", PLAYER_PATH,              # Player path (VLC)
            "-d",                                      # --debug
            "--load-playlist-from-file", playlist_path  # Load playlist file
        ]

        print(f"Executing: {' '.join([f'"{arg}"' if ' ' in arg else arg for arg in command])}")
        print(f"Name: {args.name}")
        print(f"Room: {args.room}")
        print(f"Playlist file: {playlist_path}")
        print(f"Host: {args.host}")
        print(f"Current working directory: {os.getcwd()}")

        try:
            result = subprocess.run(command, capture_output=True, text=True)
            print(f"Return code: {result.returncode}")
            
            if result.stdout:
                print("Output:")
                print(result.stdout)
            
            if result.stderr:
                print("Errors:")
                print(result.stderr)
                    
        except subprocess.TimeoutExpired:
            print("Process timed out - may be running successfully")
        except Exception as e:
            print(f"Error: {e}")

    def stream_torrent_with_syncplay():
        """Handle torrent selection, streaming, and Syncplay execution with playlist file."""
        # torrents list
        sorted_entries = getSortedLogFileEntries()
        if not sorted_entries:
            print("No torrent found.")
            print("Add a torrent first.")
            return
        print("Added torrent(s):")
        for i, d in enumerate(sorted_entries, start=1):
            entry_type = "[DIR]" if os.path.isdir(os.path.join("cached_files", d)) else "[FILE]"
            print(f'{i}- {d} {entry_type}')
        
        print("Enter the respective number to stream or 'b' to back:")
        while True:
            print("main->watch together > ", end="")
            command = input().strip()
            if command == "b":
                return
            elif not command.isdigit() or int(command) < 1 or int(command) > len(sorted_entries):
                print("Invalid input. Please enter a valid number.")
            elif command.isdigit():
                break
        
        number = int(command)
        streamLinks = retrieveStreamLinks(number=number)  
        magnetLink = retrieveMagnetLink(number=number)    
        if not streamLinks or not magnetLink:
            print("Invalid selection or missing links.")
            return
        
        # Start webtorrent in a separate command window
        os.system(f'start cmd /k webtorrent "{magnetLink}" --keep-seeding --out cached_files')
        print("Preparing playlist file...")
        time.sleep(5)  # Wait for webtorrent to initialize
        
        # Create playlist file with stream links
        playlist_path = create_playlist_file(streamLinks)
        if not playlist_path:
            print("Failed to create playlist file. Exiting.")
            return

        # Launch Syncplay with the playlist file
        playwithSyncPlay(playlist_path, NAME, ROOM, HOST)

        # Clean up playlist file after use
        if os.path.exists(PLAYLIST_PATH):
            try:
                os.remove(PLAYLIST_PATH)
                print(f"Cleaned up temporary playlist file: {PLAYLIST_PATH}")
            except Exception as e:
                print(f"Error cleaning up playlist file: {e}")
    stream_torrent_with_syncplay()

def initSyncPlay():
    if not os.path.exists("Syncplay"):
        print("Syncplay isn't installed")
        install_syncplay_portable()

def initNodeJSandWebtorrentCli():
    if install_nodejs_and_webtorrent():
        return
    else :
        print("nodejs or webtorrent installation failed")
        time.sleep(2)
        exit(1)

def requirements():
    initNodeJSandWebtorrentCli()
    clearScreen()
    initSyncPlay()
    clearScreen()
    initCacheFiles()
    load_player()
    initLog()

#main loop
requirements()
print("Ready to launch...")
while True:
    time.sleep(.5)
    clearScreen()
    print("Commands: add | play | watch together | search movie | media player | cache clear | help | exit")
    print("Enter help to know how to use\t\t\t\t\t\t\t  version - 1.1")
    print("main > ", end="")
    command = input()
    command = command.strip().lower()
    if command =="e" or command == "exit" or command=="b":
        print("Exiting...")
        sys.exit()
    elif command == "cc" or command == "cache_clear":
        cache_clear()
        print("Cache cleared.")
    elif command == "play" or command == "p":
        clearScreen()
        playConsole()
    elif command == "add" or command == "a":
        clearScreen()
        while True: 
            print("Enter the magnet link or b to back:")
            print("main->add > ", end="")
            magnet = input().strip().lower()
            
            if magnet =="b" :
                break
        
            if magnet.startswith("magnet:"):
                add(MAGNET=magnet)
                break
            else:
                print("Invalid magnet link. Please try again.\n")

    elif command=="media player" or command =="mp":
        clearScreen()
        playerSet()
    elif command=="watch together" or command =="wt":
        clearScreen()
        streamWithFriend()
    elif command=="search movie" or command =="sm":
        clearScreen()
        search_movie()
    elif command == 'h' or command == 'help':
        print("Available commands:")
        print(" add or a            - Add a new torrent via magnet link")
        print(" play or p           - Stream a torrent from the list")
        print(" watch together or wt- watch with your friend")
        print(" movie search or ms  - search a movie from yts database")
        print(" media player or mp  - selecting media player")
        print(" cache_clear or cc   - Clear cached files and logs")
        print(" help or h           - Show this help message")
        print(" exit or e           - Exit the application")
        input("Press Enter to continue...")
    else:
        print("Invalid command. Please try again.")