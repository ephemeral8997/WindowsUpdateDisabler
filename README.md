# Windows Update Service Controller

A simple GUI application to enable or disable Windows Update by modifying the ImagePath registry value.

## How it Works

The application checks the `ImagePath` value in:
```
Computer\HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\wuauserv
```

- **Enabled**: `%systemroot%\system32\svchost.exe -k netsvcs -p`
- **Disabled**: `%systemroot%\system32\svchost0.exe -k netsvcs -p`

## Features

- Displays current Windows Update service status
- Shows the actual ImagePath registry value
- One-click enable/disable functionality
- Real-time status updates
- Clean, intuitive interface

## Requirements

- Windows operating system
- Python 3.6 or higher with tkinter (usually included)
- Administrative privileges to modify registry

## Usage

1. Run the application as Administrator
2. The current status will be displayed automatically
3. Click "Enable Windows Update" or "Disable Windows Update" to toggle the service
4. Restart the Windows Update service or reboot your computer for changes to take effect

## Installation

### Option 1: Download Executable (Recommended)
Pre-built executables are available in the **GitHub Releases** section:

1. Go to the [Releases page](../../releases)
2. Download the latest `WindowsUpdateController.exe`
3. Run the executable as Administrator

**Features:**
- Clear visible buttons for enable/disable
- Real-time status display
- Registry path viewer
- Error handling for permissions
- Standalone executable (no Python required)

### Option 2: Run from Python
To run the source code:

```bash
python windows_update_disabler.py
```

### Option 3: Command Line Version
For testing without GUI:

```bash
python cli_version.py
```

**Important**: Run as Administrator for registry modification privileges.

**Important**: This application modifies Windows registry values. Use with caution and create a system backup before making changes.