import os
import time
HOST = "syncplay.pl:8999"
NAME = ""  # Default name
ROOM = ""  # Default room

def console():
        """Handle torrent selection, streaming, and Syncplay execution with playlist file."""
        # torrents list

        global NAME
        NAME = input("Enter a nickname: ")
        global ROOM
        ROOM = input("Enter room name: ")
        from utils.webtorrent_tools import retrieveMagnetLink, retrieveStreamLinks , getSortedLogFileEntries

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
        
        from utils.syncplay_integration_tools import create_playlist_file, playwithSyncPlay,PLAYLIST_PATH
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