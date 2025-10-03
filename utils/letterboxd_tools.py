from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from selenium.common.exceptions import TimeoutException

WATCHLIST_PATH = "user_data/watchlist.txt"

def login_to_letterboxd(username: str, password: str) -> webdriver.Chrome | None:
    """
    Logs into Letterboxd using a highly robust method to avoid race conditions.
    """
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    except Exception as e:
        print(f"❌ Failed to initialize WebDriver: {e}")
        return None

    try:
        print("Navigating to Letterboxd sign-in page...")
        driver.get("https://letterboxd.com/sign-in/")

        # Defensive check for cookie banner (safe to keep)
        try:
            cookie_accept_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'I Accept')]"))
            )
            print("Cookie banner found. Clicking 'I Accept'...")
            cookie_accept_button.click()
        except TimeoutException:
            print("No cookie banner found, proceeding.")
        
        # Wait for the username field to be ready
        print("Waiting for the login form to be interactable...")
        username_field = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "field-username"))
        )
        
        # ==================== ROBUST INTERACTION METHOD ====================
        # Use JavaScript to directly set the input values. This is less flaky.
        print("Entering credentials using JavaScript...")
        password_field = driver.find_element(By.ID, "field-password")
        
        driver.execute_script("arguments[0].value = arguments[1];", username_field, username)
        driver.execute_script("arguments[0].value = arguments[1];", password_field, password)
        # =================================================================

        print("Locating the 'Sign In' button...")
        sign_in_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
        )
        print("Clicking 'Sign In'...")
        # A JavaScript click can also be more reliable here
        driver.execute_script("arguments[0].click();", sign_in_button)
        
        print("Waiting for login to complete...")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, f"//a[contains(@href, '/{username}/')]"))
        )
        
        print("✅ Login successful!")
        return driver
    
    except Exception as e:
        print(f"❌ An error occurred during login: {e}")
        driver.save_screenshot("login_error.png")
        print("   Screenshot saved as 'login_error.png'")
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
        
        file = open(WATCHLIST_PATH,"w")
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
    if os.path.exists(WATCHLIST_PATH):
        with open(WATCHLIST_PATH, "r") as file:
            watchlist = file.read().splitlines()
        return watchlist
    else:
        # Create empty file if it doesn't exist
        with open(WATCHLIST_PATH, "w") as file:
            pass
        return []
    


