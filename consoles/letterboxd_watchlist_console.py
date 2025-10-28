from utils.letterboxd_tools import get_watchlist,retrieve_letterboxd_data,LetterboxdLoginManager

def console():
        # Get the watchlist
        login_manager = LetterboxdLoginManager("logins") 
        watchlist = get_watchlist()

        
        from utils.terminal_tools import clearScreen
        # Print the watchlist
        if watchlist:
            print("\nYour Letterboxd Watchlist:\n")
            i = 1 
            while i <= len(watchlist)-1:
                print(f"{i}. {watchlist[i-1]}")
                i+=1
                
            while True:
                print("\nSelect a movie or b to go back or llw to load letterboxd watchlist : ")
                choice = input("main->letterboxd watchlist > ")
                if choice == "b":
                    return
                elif choice=="llw" or choice =="load letterboxd watchlist":
                    retrieve_letterboxd_data(login_manager)
                    console()
                    return
                if choice.isdigit() and int(choice) > 0 and int(choice) <= len(watchlist):
                    selected_movie = watchlist[int(choice)-1]
                    print(f"\nSearching for: {selected_movie}")
                    break
                else:
                    print("Invalid input")
            
            # Search using search_yts method
            from utils.yts_movie_search_tools import search_yts
            movies = search_yts(selected_movie)
            
            if not movies:
                print("No results found.")
            else:
                print("\nResults: ")
                # Show movies
                for i, m in enumerate(movies, start=1):
                    print(f"{i}. {m['title']} imdb:{m['rating']}⭐")
                
                while True:
                    print("\nSelect a movie or b to back: ")
                    choice = input("main->movie search > ")
                    if choice == "b":
                        return
                    if choice.isdigit() and int(choice) <= len(movies):
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
                    print("\nSelect resolution or b to back: ")
                    t_choice = input("main->movie search > ")
                    if t_choice == "b":
                        return
                    if t_choice.isdigit() and int(t_choice) <= len(movie['torrents']):
                        t_choice = int(t_choice) - 1
                        torrent = movie['torrents'][t_choice]
                        break
                    else:
                        print("invalid input")
                
                # Generate magnet link
                from utils.yts_movie_search_tools import make_magnet
                magnet = make_magnet(torrent["hash"], torrent["movie_title"])
                from utils.webtorrent_tools import add
                add(magnet)
        
        else :
                while True:
                    print("Your watchlist is empty\nEnter load letterboxd watchlist or llw to retrieve your letterboxd watchlist\n")
                    choice = input("main->letterboxd watchlist > ")
                    if choice == "b":
                        return
                    elif choice =="load letterboxd watchlist" or choice == "llw":
                        retrieve_letterboxd_data(login_manager)
                        watchlist=get_watchlist()
                        #clearScreen()
                        console()
                        break
                    else:
                        print("invalid input\n")