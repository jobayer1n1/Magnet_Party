from utils._1377x_tools import search_torrent

def console():
    print("Enter a series name or b to back:")
    query = input("main->series search > ").strip()
    if query =="b":
        return
    serieses = search_torrent(query, limit=5, category="TV")
    
    print("\n--- 1337x ---")
    if not serieses:
        print("No results found.")
        return
    
    # Show series results
    print("\nResults:")
    for i, m in enumerate(serieses, start=1):
        print(f"{i}. {m['title']} | S:{m['seeders']} L:{m['leechers']} | {m['size']}")

    # Select a series
    while True:
        choice = input("\nSelect a series or b to back: ")
        if choice.lower() == "b":
            return
        if choice.isdigit() and 1 <= int(choice) <= len(serieses):
            series = serieses[int(choice) - 1]
            break
        else:
            print("Invalid input")

    # Show torrent info (since py1337x gives one torrent per result, just confirm)
    print(f"\nSelected: {series['title']} | Size: {series['size']} | Seeders: {series['seeders']}")
    
    # Ask to start streaming
    while True:
        choice = input("Add this torrent? (y/n): ").lower()
        if choice == "y":
            magnet = series["magnet"]
            from utils.webtorrent_tools import add
            add(magnet)  # use your webtorrent function to stream
            break
        elif choice == "n":
            return
        else:
            print("Invalid input")
