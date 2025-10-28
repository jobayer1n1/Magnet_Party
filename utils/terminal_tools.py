import os
def clearScreen():
    os.system('cls' if os.name == 'nt' else 'clear')

import os
import sys

def lock_console_window(x=100, y=100, width=800, height=600):
    try:
        # Try to import required modules
        try:
            import ctypes
            import win32gui
            import win32con
        except ImportError as e:
            print(f"Missing required modules: {e}")
            return False

        # Get the console window handle
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()

        if not hwnd:
            print("Could not get console window handle")
            return False

        print(f"Console handle: {hwnd}")

        # Disable resizing & maximize button
        try:
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            style &= ~win32con.WS_MAXIMIZEBOX  # Remove maximize button
            style &= ~win32con.WS_SIZEBOX      # Disable resizing
            style &= ~win32con.WS_THICKFRAME   # Disable thick frame
            win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)
            print("Window styles applied")
        except Exception as e:
            print(f"Failed to set window styles: {e}")

        # Force window position & size
        try:
            success = ctypes.windll.user32.MoveWindow(hwnd, x, y, width, height, True)
            print(f"Window moved: {success}")
        except Exception as e:
            print(f"Failed to move window: {e}")

        # Set console buffer size
        try:
            cols = max(80, width // 8)
            lines = max(25, height // 16)
            os.system(f'mode con: cols={cols} lines={lines}')
            print(f"Console buffer set to {cols}x{lines}")
        except Exception as e:
            print(f"Failed to set console buffer: {e}")

        # Try to bring to foreground
        try:
            win32gui.SetForegroundWindow(hwnd)
            print("Window brought to foreground")
        except Exception as e:
            print(f"Failed to set foreground: {e}")

        return True

    except Exception as e:
        print(f"Console locking completely failed: {e}")
        return False
    

import os
import winreg

def refresh_environment_variables():
    # Reload system PATH
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment") as key:
        system_path, _ = winreg.QueryValueEx(key, "Path")
    # Reload user PATH
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as key:
        try:
            user_path, _ = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            user_path = ""
    # Merge both
    new_path = system_path + ";" + user_path
    os.environ["PATH"] = new_path
