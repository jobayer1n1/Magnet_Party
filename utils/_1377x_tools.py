import py1337x

# Initialize client
torrents_client = py1337x.Py1337x()

def search_torrent(query, limit=5, category=None):
    """
    Search 1337x torrents and return a list of structured results.
    
    Each result includes:
    - title
    - seeders
    - leechers
    - size
    - torrentId
    - magnet link
    """
    results = torrents_client.search(query, category=category, sort_by='seeders',page=1)
    output = []
    
    for item in results.items:
        # Get detailed info to extract magnet link
        details = torrents_client.info(torrent_id=item.torrent_id)
        
        output.append({
            "title": item.name,
            "seeders": item.seeders,
            "leechers": item.leechers,
            "size": item.size,
            "torrentId": item.torrent_id,
            "magnet": details.magnet_link
        })
        limit-=1
        if limit==0 :
            break
    
    return output


