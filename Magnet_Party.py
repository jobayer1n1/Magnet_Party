
import sys
import time
import utils.media_player as mp
import utils.inits as inits
import utils.cache_clear as cc
import utils.stream_with_friends as sf
from utils.terminal_tools import clearScreen

def requirements():
    inits.initNodeJSandWebtorrentCli()
    inits.initSyncPlay()
    inits.initCacheFiles()
    mp.load_player()
    inits.initLog()

#main loop
requirements()
print("Launching...")
while True:
    time.sleep(.5)
    clearScreen()
    print("Commands: add magnet | play | watch together | search movie | letterbox watchlist | cache clear | help | exit")
    print("Enter help to know how to use\t\t\t\t\t\t\t\t   version - 1.1")
    print("main > ", end="")
    command = input()
    command = command.strip().lower()
    if command =="e" or command == "exit" or command=="b":
        print("Exiting...")
        sys.exit()
    elif command == "cc" or command == "cache_clear":
        cc.cache_clear()
        print("Cache cleared.")
    elif command == "play" or command == "p":
        clearScreen()
        from utils.direct_stream import playConsole
        playConsole()
    elif command == "add" or command == "a":
        clearScreen()
        from utils.add_console import connsole
        connsole()

    elif command=="lw" or command=="letterboxd watchlist":
        clearScreen()
        from utils.letterboxd_watchlist import letterboxd_watchlist
        letterboxd_watchlist()

    elif command=="media player" or command =="mp":
        clearScreen()
        mp.player_set()
    elif command=="watch together" or command =="wt":
        clearScreen()
        sf.stream_torrent_with_syncplay()
    elif command=="search movie" or command =="sm":
        clearScreen()
        from utils.torrent_search import search_movie
        search_movie()
    elif command == 'h' or command == 'help':
        print("Available commands:")
        print(" add or a            - Add a new torrent via magnet link")
        print(" play or p           - Stream a torrent from the list")
        print(" watch together or wt- watch with your friend")
        print(" movie search or ms  - search a movie from yts database")
        print(" lw                  - letterboxd watchlist")
        print(" media player or mp  - selecting media player")
        print(" cache clear or cc   - Clear cached files and logs")
        print(" help or h           - Show this help message")
        print(" exit or e           - Exit the application")
        input("Press Enter to continue...")
    else:
        print("Invalid command. Please try again.")