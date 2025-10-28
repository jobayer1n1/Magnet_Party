import os
import time
import subprocess
import argparse

LOG_FILE = "cached_files/logs.txt"
CONFIG_DIR = "configs"
PLAYER_CONFIG= "configs/player.txt"
def initLog():
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w") as f:
                f.write("")

def initConfig():
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)

        if not os.path.exists(PLAYER_CONFIG):
            with open(PLAYER_CONFIG, "w") as f:
                f.write("")

def initNodeJSandWebtorrentCli():
    from utils.nodejs_webtorrent_cli_installer import install_nodejs_and_webtorrent
    if install_nodejs_and_webtorrent():
         return
    else :
        print("nodejs or webtorrent installation failed")
        exit(1)

def initSyncPlay():

    if not os.path.exists("syncplay/syncplay.exe"):
        print("Syncplay isn't installed")
        from utils.syncplay_installer import install_syncplay_portable
        install_syncplay_portable()
        print("[IMPORTANT] setting up local host as trusted in syncplay\n"+
              "1. After launching Syncplay hit \"Store configuration and run Syncplay\" option\n"+
              "2. Wait for few seconds to load everything in Syncplay gui\n"+
              "3. Under the shared playlist checkbox your will find \"http://localhost:8000\"\n"+
              "4. Righ click on it and choose \"Add localhost as trusted domain\"\n"+
              " *If you don't do this step, media can't be played")
        
        input("\nPress enter to continue.....")
        trusted_domain_set()
        

def trusted_domain_set():
    # Construct Syncplay command
    SYNCPLAY_PATH = os.path.join("syncplay", "Syncplay.exe")
    
    # Make sure this is actually calling the function, not just referencing it
    from utils.media_player_tools import get_player_path
    PLAYER_PATH = get_player_path()  # Added parentheses to call the function
    
    command = [
        SYNCPLAY_PATH,
        "http://localhost:8000" ,
        "--host", "syncplay.pl:8999",           # More readable than -a
        "--name", "tmp",                        # -n is fine too
        "--room", "tmp",                        # -r is fine too  
        "--player-path", PLAYER_PATH,
        "--debug",
    ]

    try:
        print("Starting Syncplay...")
        process = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        
        print(f"Syncplay started with PID: {process.pid}")
        print("The script will exit when Syncplay is closed.")
        
        # Wait for the process to complete (when user exits Syncplay)
        stdout, stderr = process.communicate()
        
        print(f"Syncplay exited with return code: {process.returncode}")
        
        if stdout:
            print("Output:")
            print(stdout)
        
        if stderr:
            print("Errors:")
            print(stderr)
            
        print("Script ending...")
            
    except FileNotFoundError:
        print(f"Error: Syncplay not found at {SYNCPLAY_PATH}")
    except Exception as e:
        print(f"Error starting Syncplay: {e}")

def initCacheFiles():
    if not os.path.exists('cached_files'):
        os.makedirs('cached_files')
