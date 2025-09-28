import os
import shutil
import subprocess
import stat

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
    from utils.inits import initCacheFiles, initLog
    initCacheFiles()
    initLog()