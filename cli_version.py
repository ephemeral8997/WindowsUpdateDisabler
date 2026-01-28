import tkinter as tk
from tkinter import simpledialog, messagebox
import winreg
import sys

def main():
    print("=== Windows Update Controller ===")
    print("Checking registry...")
    
    registry_path = r"SYSTEM\CurrentControlSet\Services\wuauserv"
    value_name = "ImagePath"
    
    try:
        # Read current value
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path, 0, winreg.KEY_READ) as key:
            image_path, _ = winreg.QueryValueEx(key, value_name)
            
        print(f"\nCurrent ImagePath: {image_path}")
        
        # Check status
        if "svchost.exe" in image_path and "svchost0.exe" not in image_path:
            print("Status: ENABLED")
            choice = input("\nPress 'D' to disable, or any key to exit: ").upper()
            if choice == 'D':
                new_path = image_path.replace("svchost.exe", "svchost0.exe")
                action = "disable"
        else:
            print("Status: DISABLED")
            choice = input("\nPress 'E' to enable, or any key to exit: ").upper()
            if choice == 'E':
                new_path = image_path.replace("svchost0.exe", "svchost.exe")
                action = "enable"
            else:
                return
        
        if 'choice' in locals() and choice in ['D', 'E']:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path, 0, winreg.KEY_WRITE) as key:
                    winreg.SetValueEx(key, value_name, 0, winreg.REG_EXPAND_SZ, new_path)
                print(f"\nSuccess! Windows Update {action}d.")
                print("Restart service or computer for changes to take effect.")
            except PermissionError:
                print("\nERROR: Permission denied. Run as Administrator!")
            except Exception as e:
                print(f"\nERROR: {e}")
                
    except Exception as e:
        print(f"\nERROR reading registry: {e}")
        print("Try running as Administrator.")

if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")