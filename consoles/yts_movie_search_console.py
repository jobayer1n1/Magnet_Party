def console():
    print("Enter a movie name or b to go back:")
    query = input("main->search movie > ").strip()
    if query =="b":
        return
    from utils.yts_movie_search_tools import search_yts
    movies = search_yts(query)
    print("\nResults:")
    if not movies:
        print("No results found.")
    else:
        print("--- YTS ---")
        # Show movies

        for i, m in enumerate(movies, start=1):
            print(f"{i}. {m['title']} imdb: {m['rating']} ⭐")
        
        while True:
            print("\nSelect a movie or b to back : ")
            choice = input("main->movie search > ")
            if choice =="b":
                return
            if choice.isdigit() and int(choice)<=len(movies):
                choice = int(choice) - 1
                movie = movies[choice]
                break
            else:
                print("invalid input")
        
        print("\nResults: ")
        # Show torrents
        for j, t in enumerate(movie['torrents'], start=1):
            print(f"{j}. {t['quality']} {t['type']} | {t['size']} | S:{t['seeds']} P:{t['peers']}")
        

        while True:
            print("\nSelect resulation or b to back : ")
            t_choice = input("main->movie search > ")
            if t_choice =="b":
                return
            if t_choice.isdigit() and int(t_choice) <= len(movie['torrents']):
                t_choice = int(t_choice) - 1
                torrent = movie['torrents'][t_choice]
                break
            else : 
                print("invalid input")
        
        # Only now show magnet
        from utils.yts_movie_search_tools import make_magnet
        magnet = make_magnet(torrent["hash"], torrent["movie_title"])
        
        from utils.webtorrent_tools import add
        add(magnet)