import os
import time
import argparse
import subprocess

PLAYLIST_PATH = os.path.abspath(os.path.join("cached_files", "syncplay_playlist.txt"))
SYNCPLAY_PATH = os.path.join("syncplay", "SyncplayConsole.exe")
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

def playwithSyncPlay(playlist_path, name="", room="", host=""):
        from utils.media_player_tools import get_player_path
        PLAYER_PATH = get_player_path()
        # Set up command line argument parser
        parser = argparse.ArgumentParser(description='Run Syncplay with specified room and name')
        parser.add_argument('-n', '--name', type=str, default=name, help=f'Your display name (default: {name})')
        parser.add_argument('-r', '--room', type=str, default=room, help=f'Room to join (default: {room})')
        parser.add_argument('--host', type=str, default=host, help=f'Syncplay server host (default: {host})')
        parser.add_argument('--no-gui')
        args = parser.parse_args()
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

