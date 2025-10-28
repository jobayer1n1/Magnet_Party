import pathlib
import subprocess
import os

PLAYER_NAME=""
PLAYER_PATH=""
PLAYER_SETTING = "configs/player.txt"
def read_file_safely(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None
    
import os
import pathlib
import subprocess
from tqdm import tqdm

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
        "IINA": "iina.exe",  # Note: IINA is macOS-only, so it won't be found on Windows.
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

    # Create progress bar for checking media players.
    # The total is fixed to the number of players, so the bar advances once per player.
    with tqdm(total=len(media_players), desc="Scanning for media players", unit="player") as pbar:
        for player, executable in media_players.items():
            pbar.set_description(f"Checking {player}")
            # Clear the postfix string from the previous player
            pbar.set_postfix_str("Checking PATH...")
            found_path = None
            
            # Check if executable exists in PATH
            try:
                # Use CREATE_NO_WINDOW to prevent a console window from flashing
                result = subprocess.run(["where", executable], capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if result.stdout.strip():
                    found_path = result.stdout.split('\n')[0].strip()
                    available_players[player] = found_path
                    # Update the postfix to show the result
                    pbar.set_postfix_str("Found in PATH")
                    pbar.update(1)
                    continue
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass  # Not found in PATH, proceed to check common dirs

            # Check common installation directories if not found in PATH
            if player not in available_players:
                for base_path in common_paths:
                    try:
                        # Set postfix to show the directory currently being scanned
                        pbar.set_postfix_str(f"Scanning {base_path.name}...")
                        
                        # rglob can be slow, this text will stay visible during the scan
                        for path in base_path.rglob(executable):
                            if path.is_file():
                                found_path = str(path.resolve())
                                available_players[player] = found_path
                                # Update postfix to show where it was found
                                pbar.set_postfix_str(f"Found in {base_path.name}")
                                break
                        if found_path:
                            break
                    except (PermissionError, OSError):
                        # Couldn't scan this dir (e.g., permissions), just move to the next
                        continue

            if player not in available_players:
                # Update postfix if the player was not found after all checks
                pbar.set_postfix_str("Not found")
            
            # Advance the progress bar by one player
            pbar.update(1)

    return available_players



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
    

def load_player():
    info = read_file_safely(PLAYER_SETTING)
    if(info==None or info ==""):
        player_set()
    info = read_file_safely(PLAYER_SETTING)
    if info =="":
        print("Add a player first to launch the app")
        exit(1)
    lines = info.split("\n")
    global PLAYER_NAME
    PLAYER_NAME = lines[0]
    global PLAYER_PATH 
    PLAYER_PATH =  lines[1]
    add_to_path_temp(PLAYER_PATH)

def player_set():
    global PLAYER_NAME
    global PLAYER_PATH

    if PLAYER_NAME != "":
        print("Current Player : "+PLAYER_NAME)

        while True:
            user = input("Enter b to go back or c to change the player : ")
            if user=="b" or user=="back":
                return
            elif user=="c" or user=="change":
                break
            else:
                print("invalid input\n")

    from utils.terminal_tools import clearScreen
    clearScreen()
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

            choice = ""

            if PLAYER_NAME !="":
                print("\nChoose a player or b to back : ")
                choice = input("settings->player > ").strip()
            else:
                print("\nChoose a player : ")
                choice = input("setup->player > ").strip()
            if choice =="b" and PLAYER_NAME != "":
                return
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(players_list):
                selected_player = players_list[choice_num - 1]
                selected_path = available_players[selected_player]
                
                print(f"\nYou selected: {selected_player}")
                print(f"Executable path: {selected_path}")
                
                confirm = input("Confirm? y or yes : ").strip().lower()
                if confirm in ['y', 'yes']:
                    print(f"\nPlayer Selected Successfully\n")
                    with open(PLAYER_SETTING,"w") as file:
                            player_name = str(selected_player).lower()
                            path = str(selected_path).lower()
                            file.write(player_name+"\n"+path)
                    load_player()
                else:
                    print("Operation cancelled.")
                return
            else:
                print(f"Please enter a number between 1 and {len(players_list)}")
                
        except ValueError:
            print("Please enter a valid number.")
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            return
        
def get_player_name():
    load_player()
    return PLAYER_NAME

def get_player_path():
    load_player()
    return PLAYER_PATH

