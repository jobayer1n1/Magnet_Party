from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

import requests

BASE = "https://yts.mx/api/v2/"

def search_yts(query, limit=5):
    url = f"{BASE}list_movies.json"
    params = {"query_term": query, "limit": limit}
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
            "torrents": torrents
        })
    return results

def make_magnet(hashcode, title):
    return (
        f"magnet:?xt=urn:btih:{hashcode}"
        f"&dn={title.replace(' ', '+')}"
        f"&tr=udp://tracker.openbittorrent.com:80/announce"
    )

def search_movie(query=""):
    movies = search_yts(query)
    
    if not movies:
        print("No results found.")
    else:
        # Show movies
        for i, m in enumerate(movies, start=1):
            print(f"{i}. {m['title']} ({m['year']}) ⭐ {m['rating']}")
        
        choice = int(input("\nSelect movie number: ")) - 1
        movie = movies[choice]
        
        # Show torrents
        for j, t in enumerate(movie['torrents'], start=1):
            print(f"{j}. {t['quality']} {t['type']} | {t['size']} | S:{t['seeds']} P:{t['peers']}")
        
        t_choice = int(input("\nSelect torrent number: ")) - 1
        torrent = movie['torrents'][t_choice]
        
        # Only now show magnet
        magnet = make_magnet(torrent["hash"], torrent["movie_title"])
        print("\nMagnet link:")
        print(magnet)

def clearScreen():
    os.system('cls' if os.name == 'nt' else 'clear')

def login_to_letterboxd(username, password):
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-software-rasterizer")
    
    # Set up the Selenium WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        # Navigate to Letterboxd login page
        print("Navigating to Letterboxd login page...")
        driver.get("https://letterboxd.com/sign-in/")
        
        # Wait for the username field to be visible and enter credentials
        print("Waiting for username field...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        username_field = driver.find_element(By.NAME, "username")
        password_field = driver.find_element(By.NAME, "password")
        
        print("Entering username and password...")
        username_field.send_keys(username)
        password_field.send_keys(password)
        
        # Find and click the "Sign In" button
        print("Locating Sign In button...")
        sign_in_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit'], input[type='submit'], button.sign-in-button, input[value*='Sign in']"))
        )
        print("Sign In button found, clicking...")
        sign_in_button.click()
        
        # Wait for login confirmation
        print("Waiting for login to complete...")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, f"//a[contains(@href, '/{username}/')]"))
        )
        print("Login confirmed!")
        return driver
    
    except Exception as e:
        print(f"Login failed: {e}")
        driver.save_screenshot("login_error.png")
        print("Screenshot saved as login_error.png")
        driver.quit()
        return None

def retrieve_letterboxd_watchlist():
    username = input("Enter your Letterboxd username: ")
    password = input("Enter your Letterboxd password: ")
    
    # Log in to Letterboxd
    driver = login_to_letterboxd(username, password)
    try:
        # Navigate to the user's watchlist page
        watchlist_url = f"https://letterboxd.com/{username}/watchlist/"
        print(f"Navigating to watchlist: {watchlist_url}")
        driver.get(watchlist_url)
        
        # Wait for the watchlist films to load
        print("Waiting for watchlist to load...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "grid"))
        )
        print("Watchlist page loaded.")
        
        # Scroll to load all films
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        print("Finished scrolling watchlist.")
        time.sleep(5)  # Additional delay for dynamic content
        
        # Extract film titles
        film_elements = driver.find_elements(By.CSS_SELECTOR, ".grid .frame")
        print(f"Found {len(film_elements)} film elements.")
        watchlist = []
        for element in film_elements:
            try:
                # Get title from data-original-title attribute
                title = element.get_attribute("data-original-title")
                if not title:
                    # Fallback to frame-title span if data-original-title is missing
                    title_span = element.find_element(By.CLASS_NAME, "frame-title")
                    title = title_span.text.strip()
                if title:
                    watchlist.append(title)
                else:
                    print(f"No title found for element: {element.get_attribute('outerHTML')}")
            except Exception as e:
                print(f"Error processing element: {e}, HTML: {element.get_attribute('outerHTML')}")
        
        if not watchlist:
            driver.save_screenshot("watchlist_error.png")
            print("Screenshot saved as watchlist_error.png")
        
        movies =""
        for movie in watchlist :
            movies+=movie+"\n"
        
        file = open("watchlist.txt","w")
        file.write(movies)
        file.close()

    except Exception as e:
        print(f"Error retrieving watchlist: {e}")
        driver.save_screenshot("watchlist_error.png")
        print("Screenshot saved as watchlist_error.png")
        return []
    
    finally:
        driver.quit()

def load_watchlist():
    if os.path.exists("watchlist.txt"):
        with open("watchlist.txt", "r") as file:
            watchlist = file.read().splitlines()
        return watchlist
    else:
        # Create empty file if it doesn't exist
        with open("watchlist.txt", "w") as file:
            pass
        return []

def letterboxd_watchlist():
        # Get the watchlist
        watchlist = load_watchlist()
        
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
                    retrieve_letterboxd_watchlist()
                    letterboxd_watchlist()
                    return
                if choice.isdigit() and int(choice) > 0 and int(choice) <= len(watchlist):
                    selected_movie = watchlist[int(choice)-1]
                    print(f"\nSearching for: {selected_movie}")
                    break
                else:
                    print("Invalid input")
            
            # Search using search_yts method
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
                magnet = make_magnet(torrent["hash"], torrent["movie_title"])
                print("\nMagnet link:")
                print(magnet)
        
        else :
                while True:
                    print("Your watchlist is empty\nEnter load letterboxd watchlist or llw to retrieve your letterboxd watchlist")
                    choice = input("main->letterboxd watchlist > ")
                    if choice == "b":
                        return
                    elif choice =="load letterboxd watchlist" or choice == "llw":
                        retrieve_letterboxd_watchlist()
                        watchlist=load_watchlist()
                        break
                    else:
                        print("invalid input\n")

if __name__ == "__main__":
    letterboxd_watchlist()