import os

def console():
    from utils.webtorrent_tools import getSortedLogFileEntries

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
    from utils.webtorrent_tools import stream
    stream(number=line)
