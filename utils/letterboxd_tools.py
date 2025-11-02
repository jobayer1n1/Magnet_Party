from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import zipfile
from selenium.common.exceptions import TimeoutException
import csv
from pathlib import Path
import tempfile
from tqdm import tqdm
import shutil


WATCHLIST_PATH = "letterboxd_data/watchlist.csv" 
DATA_DIR  = Path("letterboxd_data")
DOWNLOAD_DIR = Path(tempfile.mkdtemp(prefix="letterboxd_export_"))
    
def get_watchlist():
    """
    Reads the watchlist.csv file and returns a list of film titles.
    Assumes the first column after the header contains the titles.
    """
    file_path = WATCHLIST_PATH
    watchlist = []
    if not os.path.exists(file_path):
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)  # Skip header
            for row in reader:
                if row:  # Non-empty row
                    title = row[1].strip() if row[1] else ""
                    if title:
                        watchlist.append(title)
    except Exception as e:
        print(f"Error reading CSV: {e}")
    watchlist.sort()
    return watchlist


def login_to_letterboxd(username: str, password: str, chrome_options=None, pbar=None, task_weights=None) -> webdriver.Chrome | None:
    """
    Logs into Letterboxd with progress bar integration.
    """
    driver = None
    if task_weights ==None :
        task_weights = [10,10,10,10,25,35]

        # Login tasks
    login_tasks = [
            ("🌐 Loading sign-in page", task_weights[0]),
            ("📋 Waiting for login form", task_weights[1]),
            ("🍪 Handling cookies", task_weights[2]),
            ("🔑 Entering credentials", task_weights[3]),
            ("📤 Submitting form", task_weights[4]),
            ("✅ Verifying login", task_weights[5]),
        ]
        

    if pbar == None:
        total_steps = sum(weight for _, weight in login_tasks)
        internal_pbar = None
        if pbar is None:
            internal_pbar = tqdm(total=total_steps, desc="Letterboxd Login", unit="step",
                        bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]')
            pbar = internal_pbar
            
    if chrome_options == None:
            # Configure browser options for download - ALWAYS HEADLESS
            chrome_options = webdriver.ChromeOptions()
            # Essential headless arguments
            chrome_options.add_argument("--headless=new")  # Use new headless mode
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            prefs = {
                "download.default_directory": str(DOWNLOAD_DIR.absolute()),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
                "profile.default_content_settings.popups": 0,
            }
            chrome_options.add_experimental_option("prefs", prefs)

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    except Exception as e:
        print("something went wrong")
        return None

    try:

        # Task 1: Navigate to sign-in page
        pbar.set_description("🌐 Loading sign-in page")
        driver.get("https://letterboxd.com/sign-in/")
        WebDriverWait(driver, 30).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        pbar.update(login_tasks[0][1])
        
        # Task 2: Wait for login form
        pbar.set_description("📋 Waiting for login form")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "form.js-sign-in-form"))
        )
        pbar.update(login_tasks[1][1])
        
        # Task 3: Handle cookie banner
        pbar.set_description("🍪 Handling cookies")
        try:
            cookie_buttons = WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.XPATH, "//button[contains(., 'Accept') or contains(., 'I Accept') or contains(., 'Agree')]"))
            )
            if cookie_buttons:
                driver.execute_script("arguments[0].click();", cookie_buttons[0])
                time.sleep(1)
        except TimeoutException:
            pass
        pbar.update(login_tasks[2][1])
        
        # Task 4: Fill credentials
        pbar.set_description("🔑 Entering credentials")
        form = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "form.js-sign-in-form"))
        )
        
        username_field = form.find_element(By.ID, "field-username")
        password_field = form.find_element(By.ID, "field-password")
        
        driver.execute_script("arguments[0].value = arguments[1];", username_field, username)
        driver.execute_script("arguments[0].value = arguments[1];", password_field, password)
        pbar.update(login_tasks[3][1])
        
        # Task 5: Submit form
        pbar.set_description("📤 Submitting form")
        submit_button = form.find_element(By.CSS_SELECTOR, "button[type='submit']")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_button)
        driver.execute_script("arguments[0].click();", submit_button)
        pbar.update(login_tasks[4][1])
        
        # Task 6: Verify login
        pbar.set_description("✅ Verifying login")
        time.sleep(3)
        
        def check_logged_in():
            try:
                current_url = driver.current_url
                
                # Check URL patterns for successful login
                success_urls = [
                    '/home', '/', '/films', '/activity', 
                    f'/{username}', f'/{username}/'
                ]
                
                if any(success_url in current_url for success_url in success_urls):
                    return True
                
                # Check for logged-in user elements
                logged_in_selectors = [
                    f"a[href*='/{username}']",
                    ".avatar",
                    "#nav-you",
                    ".logged-in",
                    ".icon-avatar",
                    "[data-target='you-menu']",
                ]
                
                for selector in logged_in_selectors:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements and any(el.is_displayed() for el in elements):
                            return True
                    except:
                        continue
                
                # Check page content
                page_source = driver.page_source
                if 'Sign in' not in driver.title and 'sign-in' not in current_url:
                    if 'Log out' in page_source or 'Sign out' in page_source:
                        return True
                
                # Check for username on page
                if 'sign-in' not in current_url:
                    try:
                        user_indicators = driver.find_elements(By.XPATH, f"//*[contains(text(), '{username}')]")
                        if user_indicators:
                            return True
                    except:
                        pass
                
                return False
                
            except Exception:
                return False

        # Wait for login verification
        max_wait = 30
        start_time = time.time()
        login_verified = False
        
        while time.time() - start_time < max_wait:
            if check_logged_in():
                login_verified = True
                break
            
            # Check for errors
            try:
                error_selectors = [
                    ".error", ".alert", ".message.-error", 
                    "[class*='error']", "[class*='alert']",
                    ".standalone-flow-message"
                ]
                for selector in error_selectors:
                    errors = driver.find_elements(By.CSS_SELECTOR, selector)
                    for error in errors:
                        if error.is_displayed() and error.text.strip():
                            if len(error.text.strip()) > 10:
                                driver.save_screenshot("login_error_detected.png")
                                driver.quit()
                                return None
            except:
                pass
            
            time.sleep(2)
        
        # Final verification attempt
        if not login_verified:
            try:
                driver.get("https://letterboxd.com/")
                time.sleep(3)
                login_verified = check_logged_in()
            except:
                pass
        
        if not login_verified:
            driver.save_screenshot("login_verification_failed.png")
            driver.quit()
            return None
        
        pbar.update(login_tasks[5][1])
        return driver

    except Exception as e:
        driver.save_screenshot("login_unexpected_error.png")
        driver.quit()
        return None

def retrieve_letterboxd_data(login_manager):
    """
    Main function to export Letterboxd data with unified progress bar.
    """
    
    login_data = select_login(login_manager) 
    if not login_data:
        tmp = input("Enter 'a' to add new login or any other key to go back: ").strip().lower()
        if tmp == 'a':
            add_new_login(login_manager)
            from utils.terminal_tools import clearScreen
            clearScreen()
            login_data = select_login(login_manager)
        else :
            return None
    
    if not login_data:
        return None
        
    username = login_data['username']
    password = login_data['password']

    driver = None
    try:
        print("Your letterboxd data is being retrieved...")
        
        # Create directories first
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        # Configure browser options
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        prefs = {
            "download.default_directory": str(DOWNLOAD_DIR.absolute()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.default_content_settings.popups": 0,
        }
        options.add_experimental_option("prefs", prefs)

        # Try login first without progress bar to see where it fails
        driver = login_to_letterboxd(username, password, options)
        
        if not driver:
            return None
            
        
        # Navigate to export page

        export_url = "https://letterboxd.com/user/exportdata/"
        driver.get(export_url)
        

        try:
            export_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.button.-action.button-action.export-data-button"))
            )
        except Exception as e:
            print(f"DEBUG: Could not find export button: {e}")
            # Take screenshot to see what's on the page
            driver.save_screenshot("export_page_debug.png")
            print("DEBUG: Saved screenshot as 'export_page_debug.png'")
            return None

        # Get initial list of files
        initial_zips = set()
        if DOWNLOAD_DIR.exists():
            initial_zips = {f for f in DOWNLOAD_DIR.iterdir() if f.is_file() and f.suffix == '.zip'}

        # Click export button
        export_button.click()
        
        # Wait for download
        timeout = 90
        start_time = time.time()
        zip_path = None
        
        while time.time() - start_time < timeout:
            time.sleep(3)
            elapsed = int(time.time() - start_time)
            
            if not DOWNLOAD_DIR.exists():
                continue
                
            current_zips = {f for f in DOWNLOAD_DIR.iterdir() if f.is_file() and f.suffix == '.zip'}
            new_zips = current_zips - initial_zips
            
            for zip_file in new_zips:
                # Skip if still downloading
                if zip_file.name.endswith(('.crdownload', '.part')):
                    continue
                
                # Try to open the ZIP file
                try:
                    with zipfile.ZipFile(zip_file, 'r') as test_zip:
                        file_list = test_zip.namelist()
                        if file_list:
                            zip_path = zip_file
                            break
                except (zipfile.BadZipFile, OSError) as e:
                    continue
            
            if zip_path:
                break
        
        if not zip_path:
            # List all files in download directory for debugging
            if DOWNLOAD_DIR.exists():
                all_files = list(DOWNLOAD_DIR.iterdir())
            return None
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            for file in file_list:
                zip_ref.extract(file, DATA_DIR)
        
        # Verify extraction
        csv_files = list(DATA_DIR.glob("*.csv"))
            
        if csv_files:
            return DATA_DIR
        else:
            return None
        
    except Exception as e:
        print(f"DEBUG: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        
        if driver:
            driver.save_screenshot("retrieval_error.png")
        return None
    finally:
        # Cleanup
        if DOWNLOAD_DIR.exists():
            shutil.rmtree(DOWNLOAD_DIR)
        if driver:
            driver.quit()

import os
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import getpass

class LetterboxdLoginManager:
    def __init__(self, logins_dir="logins"):
        self.logins_dir = logins_dir
        self.master_key_file = os.path.join(logins_dir, ".master.key")
        os.makedirs(logins_dir, exist_ok=True)
        
    def _get_master_key(self):
        """Get or create master encryption key"""
        if os.path.exists(self.master_key_file):
            with open(self.master_key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(self.master_key_file, 'wb') as f:
                f.write(key)
            os.chmod(self.master_key_file, 0o600)
            return key
    
    def _encrypt_password(self, password: str) -> str:
        """Encrypt password using Fernet"""
        key = self._get_master_key()
        fernet = Fernet(key)
        encrypted = fernet.encrypt(password.encode())
        return base64.b64encode(encrypted).decode()
    
    def _decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt password using Fernet"""
        key = self._get_master_key()
        fernet = Fernet(key)
        encrypted = base64.b64decode(encrypted_password.encode())
        return fernet.decrypt(encrypted).decode()
    
    def save_login(self, username: str, password: str):
        """Save Letterboxd login credentials"""
        login_file = os.path.join(self.logins_dir, f"{username}.json")
        
        login_data = {
            'username': username,
            'password': self._encrypt_password(password),
            'service': 'letterboxd'
        }
        
        with open(login_file, 'w') as f:
            json.dump(login_data, f, indent=2)
        
        # Set restrictive permissions
        os.chmod(login_file, 0o600)
    
    def get_saved_usernames(self):
        """Get list of all saved usernames"""
        usernames = []
        for file in os.listdir(self.logins_dir):
            if file.endswith('.json') and file != '.master.key':
                username = file.replace('.json', '')
                usernames.append(username)
        return sorted(usernames)
    
    def get_login(self, username: str):
        """Get decrypted login credentials for a username"""
        login_file = os.path.join(self.logins_dir, f"{username}.json")
        
        if not os.path.exists(login_file):
            return None
        
        with open(login_file, 'r') as f:
            login_data = json.load(f)
        
        # Decrypt the password
        login_data['password'] = self._decrypt_password(login_data['password'])
        return login_data
    
    def delete_login(self, username: str):
        """Delete saved login"""
        login_file = os.path.join(self.logins_dir, f"{username}.json")
        if os.path.exists(login_file):
            os.remove(login_file)
            print(f"Login deleted for user: {username}")
        else:
            print(f"No saved login found for user: {username}")


def display_saved_logins(login_manager):
    """Display all saved usernames"""
    usernames = login_manager.get_saved_usernames()
    
    if not usernames:
        print("\nNo saved logins found.")
        return []
    
    print("\n📝 Saved Letterboxd Logins:")
    print("-" * 30)
    for i, username in enumerate(usernames, 1):
        print(f"{i}. {username}")
    print("-" * 30)
    
    return usernames

def select_login(login_manager):
    """Let user select a saved login"""
    usernames = display_saved_logins(login_manager)
    
    if not usernames:
        return None
    
    while True:
        try:
            choice = input("\nSelect login (number) or 'c' to cancel: ").strip().lower()
            
            if choice == 'c':
                return None
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(usernames):
                selected_username = usernames[choice_num - 1]
                login_data = login_manager.get_login(selected_username)
                
                print(f"\nSelected login: {selected_username}")
                return login_data
            else:
                print("Invalid selection. Please try again.")
                
        except ValueError:
            print("Please enter a valid number or 'c' to cancel.")

def add_new_login(login_manager):
    """Add a new Letterboxd login"""
    print("\n➕ Add New Letterboxd Login")
    print("-" * 30)
    
    print("Enter your Letterboxd credentials or press enter to go back:")
    username = input("Letterboxd Username: ").strip()

    if not username:
        return
    

    # Check if username already exists
    if username in login_manager.get_saved_usernames():
        overwrite = input(f"Login for '{username}' already exists. Overwrite? (y/n): ").strip().lower()
        if overwrite != 'y':
            return
    
    password = getpass.getpass("Letterboxd Password: ")
    
    if not password:
        print("Password cannot be empty!")
        return
    
    # Confirm password
    confirm_password = getpass.getpass("Confirm Password: ")
    
    if password != confirm_password:
        print("Passwords do not match!")
        return
    
    print("\nChecking if it's valid...")
    driver = login_to_letterboxd(username,password)

    if driver ==None:
        print("[error] check your username and password.")
        return
    
    login_manager.save_login(username, password)

def letterboxd_login_manager_console():
    login_manager = LetterboxdLoginManager("logins")
    
    while True:
        from utils.terminal_tools import clearScreen
        clearScreen()
        print("Letterboxd Login Manager")
        print("1. View Saved Logins")
        print("2. Add New Login")
        print("3. Delete Login")

        print("\nEnter a choice (1/2/3) or b to go back:")
        choice = input("main->letterboxd login manager > ").strip().lower()
        from utils.terminal_tools import clearScreen
        if choice == '1':
            clearScreen()
            display_saved_logins(login_manager)
            input("\nPress enter to go back to the manager...")
        elif choice == '2':
            clearScreen()
            add_new_login(login_manager)
        elif choice == '3':
            clearScreen()
            usernames = display_saved_logins(login_manager)
            if usernames:
                del_choice = input("Enter username to delete or 'c' to cancel: ").strip()
                if del_choice in usernames:
                    login_manager.delete_login(del_choice)
                elif del_choice.lower() == 'c':
                    continue
                else:
                    print("Username not found.")
            input("\nPress enter to go back to the manager...")
        elif choice == 'b':
            return
        else:
            print("Invalid input. Please try again.\n")