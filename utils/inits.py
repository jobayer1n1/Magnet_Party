import os
import utils.nodejs_webtorrent_cli_installer as nw
import utils.syncplay_installer as syncplay

LOG_FILE = "cached_files/logs.txt"
def initLog():
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w") as f:
                f.write("")

def initNodeJSandWebtorrentCli():
    if nw.install_nodejs_and_webtorrent():
        return
    else :
        print("nodejs or webtorrent installation failed")
        exit(1)

def initSyncPlay():
    if not os.path.exists("Syncplay"):
        print("Syncplay isn't installed")
        syncplay.install_syncplay_portable()

def initCacheFiles():
    if not os.path.exists('cached_files'):
        os.makedirs('cached_files')