def connsole():    
    while True: 
        print("Enter the magnet link or b to back:")
        print("main->add > ", end="")
        magnet = input().strip().lower()
            
        if magnet =="b" :
                break
        
        if magnet.startswith("magnet:"):
            from utils.media_tools import add
            add(MAGNET=magnet)
            break
        else:
            print("Invalid magnet link. Please try again.\n")