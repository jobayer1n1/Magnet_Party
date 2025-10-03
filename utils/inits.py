import os

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
    if not os.path.exists("Syncplay"):
        print("Syncplay isn't installed")
        from utils.syncplay_installer import install_syncplay_portable
        install_syncplay_portable()

def initCacheFiles():
    if not os.path.exists('cached_files'):
        os.makedirs('cached_files')