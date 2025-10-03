import requests

YTS_API = "https://yts.mx/api/v2/"

def search_yts(query,limit=5):
    url = f"{YTS_API}list_movies.json"
    params = {"query_term": query,"limit":limit}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    
    if data["status"] != "ok" or not data["data"]["movie_count"]:
        return []
    
    results = []
    for movie in data["data"]["movies"]:
        torrents = []
        for t in movie.get("torrents", []):
            torrents.append({
                "quality": t["quality"],
                "type": t["type"],
                "size": t["size"],
                "seeds": t["seeds"],
                "peers": t["peers"],
                "hash": t["hash"],
                "movie_title": movie["title_long"]
            })
        results.append({
            "title": movie["title_long"],
            "year": movie["year"],
            "rating": movie["rating"],
            "seeds" : t["seeds"],
            "peers" : t["peers"],
            "torrents": torrents
        })
    return results

def make_magnet(hashcode, title):
    return (
        f"magnet:?xt=urn:btih:{hashcode}"
        f"&dn={title.replace(' ', '+')}"
        f"&tr=udp://tracker.openbittorrent.com:80/announce"
    )