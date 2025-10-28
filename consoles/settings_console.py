from utils.media_player_tools import player_set
from utils.terminal_tools import clearScreen

def console():
    while True:
        clearScreen()
        print("1. Media Player Settings")
        print("2. Letterboxd Login Manager\n")
        print("Enter a choice (1/2) or b to back:")
        choice = input("main->settings > ").strip().lower()
        if choice == "1" or choice == "mps":
            clearScreen()
            player_set()
        elif choice == "2" or choice == "llm":
            clearScreen()
            from utils.letterboxd_tools import letterboxd_login_manager_console
            letterboxd_login_manager_console()
        elif choice == "b":
            return
        else:
            print("Invalid input")
            input("Press Enter to continue...")