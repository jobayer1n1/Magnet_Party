from ctypes import wintypes
import ctypes
import requests
import shutil
import os
import tempfile
import platform
import subprocess

def run_as_admin_and_wait(command):
    """
    Run a command in a new elevated terminal window (Admin privileges)
    and wait until it finishes.
    """
    SEE_MASK_NOCLOSEPROCESS = 0x00000040

    class SHELLEXECUTEINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("fMask", wintypes.ULONG),
            ("hwnd", wintypes.HWND),
            ("lpVerb", wintypes.LPCWSTR),
            ("lpFile", wintypes.LPCWSTR),
            ("lpParameters", wintypes.LPCWSTR),
            ("lpDirectory", wintypes.LPCWSTR),
            ("nShow", ctypes.c_int),
            ("hInstApp", wintypes.HINSTANCE),
            ("lpIDList", wintypes.LPVOID),
            ("lpClass", wintypes.LPCWSTR),
            ("hkeyClass", wintypes.HKEY),
            ("dwHotKey", wintypes.DWORD),
            ("hIcon", wintypes.HANDLE),
            ("hProcess", wintypes.HANDLE),
        ]

    shell32 = ctypes.windll.shell32
    sei = SHELLEXECUTEINFO()
    sei.cbSize = ctypes.sizeof(sei)
    sei.fMask = SEE_MASK_NOCLOSEPROCESS
    sei.hwnd = None
    sei.lpVerb = "runas"            # force admin
    sei.lpFile = "cmd.exe"
    sei.lpParameters = f"/c {command}"
    sei.lpDirectory = None
    sei.nShow = 1  # SW_SHOWNORMAL

    if not shell32.ShellExecuteExW(ctypes.byref(sei)):
        raise ctypes.WinError()

    # Wait until process finishes
    kernel32 = ctypes.windll.kernel32
    kernel32.WaitForSingleObject(sei.hProcess, -1)

    exit_code = wintypes.DWORD()
    kernel32.GetExitCodeProcess(sei.hProcess, ctypes.byref(exit_code))
    kernel32.CloseHandle(sei.hProcess)

    return exit_code.value == 0


def install_nodejs():
    """Download Node.js MSI and run installer in elevated terminal, wait for it to finish."""
    arch = "x64" if platform.architecture()[0] == "64bit" else "x86"
    node_version = "18.20.4"
    node_url = f"https://nodejs.org/dist/v{node_version}/node-v{node_version}-{arch}.msi"

    temp_dir = tempfile.gettempdir()
    installer_path = os.path.join(temp_dir, "node-installer.msi")

    print("⬇ Downloading Node.js installer...")
    response = requests.get(node_url, stream=True, timeout=60)
    if response.status_code == 200:
        with open(installer_path, "wb") as f:
            shutil.copyfileobj(response.raw, f)
        print(f"✔ Node.js installer saved to {installer_path}")
    else:
        raise RuntimeError(f"Failed to download Node.js installer (HTTP {response.status_code})")

    cmd = f'msiexec /i "{installer_path}" /quiet /norestart'
    return run_as_admin_and_wait(cmd)


def install_webtorrent():
    """Install webtorrent-cli globally in elevated terminal, wait for it to finish."""
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    cmd = f'{npm_cmd} install -g webtorrent-cli'
    return run_as_admin_and_wait(cmd)


def install_nodejs_and_webtorrent():
    """Ensure Node.js and webtorrent-cli are installed in sequence."""

    def run_command(cmd):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True,shell=True)
            return True, result.stdout.strip()
        except Exception:
            return False, None

    def check_node():
        ok, out = run_command(["node", "--version"])
        if ok:
            return True
        else:
            print("✘ Node.js not found.")
            return False


    def check_webtorrent():
        ok, out = run_command(["webtorrent", "--version"])
        if ok:
            return True
        else:
            print("✘ webtorrent-cli not found.")
            return False


    node_ok = check_node()
    webtorrent_ok = check_webtorrent()

    if node_ok and webtorrent_ok:
        return True

    if not node_ok:
        print("Node.js missing → launching installer (waiting)...")
        if not install_nodejs():
            print("Node.js installation failed.")
            return False
        print("Node.js installed successfully.")

    if not webtorrent_ok:
        print("")
        print("webtorrent-cli missing → launching installer (waiting)...")
        if not install_webtorrent():
            print("webtorrent-cli installation failed.")
            return False
        print("webtorrent-cli installed successfully.")

    print("Node.js and webtorrent-cli are installed.\n")
    return True