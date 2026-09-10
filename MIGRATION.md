# SceneKraft 2.0 - Complete Rewrite Documentation

## 1. WHAT WAS WRONG

### Critical Architectural Problems

**Event Loop Conflict** (The Core Issue)
- The original code called `webview.start()` from a Tkinter button callback
- Tkinter already owns the main event loop
- pywebview also wants to own the GUI event loop
- Result: Blocking the Tkinter thread, unresponsive UI, or deadlock
- **Fix:** Separate processes - Tkinter in main process, pywebview in subprocess

**Single Process, Multiple Event Loops**
- Trying to run both Tkinter and pywebview in the same process
- Each framework needs its own event loop to function
- Impossible to coordinate without one blocking the other

**Global State Management**
- Used global variables: `wallpaper_window`, `wallpaper_running`, `stop_requested`
- No clear ownership model
- Hard to track state across threads
- **Fix:** Encapsulated state in `WallpaperProcessManager` class

**Unreliable Window Discovery**
- Only used window title lookup: `FindWindowW(None, "SceneKraft Wallpaper")`
- Window title lookups are notoriously unreliable
- **Fix:** Process ID based subprocess management, fallback to title if needed

**No Error Handling or Logging**
- Widespread `except Exception: pass` statements
- Errors silently swallowed with no trace
- No log file for debugging
- **Fix:** Comprehensive logging to `~/.scenekraft/scenekraft.log`

**WorkerW Attachment Incomplete**
- Simply called `SetParent(hwnd, workerw)` without proper window configuration
- Didn't always set correct window styles
- Didn't handle case when WorkerW not found
- **Fix:** Robust desktop attachment with proper window style configuration

**Process Cleanup Issues**
- No mechanism to reliably terminate wallpaper process
- Could leave orphaned processes
- **Fix:** Proper subprocess management with terminate/kill logic

**Startup Path Problems**
- Used `sys.executable` directly without handling PyInstaller case
- Didn't work correctly when packaged as .exe
- **Fix:** Detection for PyInstaller with fallback logic

**No Configuration Error Handling**
- Used plain text file (`wallpaper.txt`)
- Silent failures on I/O errors
- No validation
- **Fix:** JSON config with proper error handling and logging

**WebView2 Runtime Not Checked**
- No detection if Microsoft Edge WebView2 was missing
- Application would silently fail with cryptic error
- **Fix:** Proper error logging and user-facing messages

---

## 2. WHAT YOU CHANGED

### Architecture Redesign

**Multi-Process Architecture**
```
Main Process (Tkinter)
├─ Owns Tkinter event loop
├─ Manages file selection UI
├─ Handles configuration
├─ Manages Windows startup registry
└─ Spawns/monitors wallpaper subprocess

Wallpaper Process (pywebview)
├─ Runs independently via subprocess
├─ Creates pywebview window
├─ Calls webview.start() normally
├─ Finds native HWND
├─ Attaches to WorkerW
└─ Displays HTML as wallpaper
```

**Process Management**
- Replaced threading and global state with `subprocess.Popen`
- `WallpaperProcessManager` class encapsulates all subprocess logic
- Clean start/stop/restart interface
- Timeout-based termination with force kill fallback

**Configuration Management**
- `Config` class handles persistent settings
- JSON format (`~/.scenekraft/config.json`)
- Proper error handling and validation
- Separate saving/loading methods

**Windows Startup Handling**
- `Startup` class manages registry operations
- Detects PyInstaller executable vs Python script
- Handles pythonw.exe fallback for console hiding
- Clear error reporting

**Windows API Abstraction**
- `WindowsAPI` class encapsulates all ctypes calls
- Robust error handling for each Windows call
- Proper logging of API failures
- Virtual screen detection for multi-monitor support

**Logging System**
- Python's `logging` module to `~/.scenekraft/scenekraft.log`
- Both file and console output
- Comprehensive exception tracebacks
- Information at each step for debugging

**Desktop Attachment (WorkerW)**
- Improved `find_workerw()` with better enumeration
- Proper window style configuration (GWL_STYLE changes)
- Correct use of `SetParent()` followed by `SetWindowPos()`
- Multi-monitor virtual desktop support
- Clear error messages if WorkerW not found

**IPC Between Processes**
- Simple file-based IPC: HWND written to `~/.scenekraft/wallpaper_hwnd.txt`
- Manager process can read wallpaper HWND if needed
- Reliable and doesn't require complex IPC primitives

**Startup Mode Improvements**
- Only loads wallpaper at startup if file still exists
- Shows manager window if no valid wallpaper
- Waits 3 seconds for Windows Explorer initialization
- Logged startup sequence

**Process Monitoring**
- Manager monitors wallpaper subprocess with polling
- Detects crashes via `.poll()` checks
- Updates UI if process dies unexpectedly
- Prevents infinite restart loops

---

## 3. INSTALLATION

### Prerequisites
- Windows 10 or Windows 11
- Python 3.8+ (or PyInstaller .exe)
- Microsoft Edge WebView2 runtime (if not already installed)

### Step 1: Install Dependencies

```bash
pip install pywebview
```

That's it! Only one dependency needed.

### Step 2: Verify Installation

```bash
python app.py
```

The SceneKraft manager window should appear.

### Step 3: Check WebView2

If you see errors about WebView2:
1. Download WebView2 runtime from: https://developer.microsoft.com/en-us/microsoft-edge/webview2/
2. Install the "Evergreen Runtime" (recommended)
3. Restart the application

### Optional: Create a Shortcut

Create a Windows shortcut to `app.py`:
- Target: `C:\Python\pythonw.exe C:\path\to\app.py`
- (This hides the console window)

---

## 4. HOW TO TEST

### Test 1: Basic UI and File Selection

1. **Launch the manager:**
   ```bash
   python app.py
   ```

2. **Test file selection:**
   - Click "BROWSE COMPUTER"
   - Select a simple HTML file (create one if needed)
   - Verify filename appears in the card

3. **Check status updates:**
   - Status should change to "● Wallpaper selected" (blue)

### Test 2: Wallpaper Creation (Create Test HTML)

Create a test file called `test_wallpaper.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Test Wallpaper</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            overflow: hidden;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: Arial, sans-serif;
            color: white;
        }
        h1 {
            font-size: 48px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }
    </style>
</head>
<body>
    <h1>SceneKraft Test Wallpaper</h1>
    <script>
        console.log("Wallpaper loaded!");
    </script>
</body>
</html>
```

### Test 3: Enable Wallpaper

1. **Select the test HTML file** in the manager
2. **Click "ENABLE WALLPAPER"**
3. **Observe:**
   - Status changes to "● Loading wallpaper..." (yellow)
   - After 2-3 seconds: "● Wallpaper enabled" (green)
   - Desktop shows gradient wallpaper behind icons

### Test 4: Disable Wallpaper

1. **Click "DISABLE WALLPAPER"**
2. **Observe:**
   - Status changes to "● Wallpaper disabled" (red)
   - Desktop returns to normal

### Test 5: Enable → Disable → Enable Cycle

1. Enable wallpaper
2. Verify it appears
3. Disable wallpaper
4. Verify desktop is normal
5. Enable again
6. Verify it appears again
7. No orphaned processes should remain

### Test 6: Windows Startup

1. **Check the "Start SceneKraft with Windows" checkbox**
2. **Observe:**
   - Status text changes to "Enabled" (green)
   - Manager should log this to `~/.scenekraft/scenekraft.log`

3. **Verify registry:**
   - Open RegEdit
   - Navigate to: `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`
   - Look for "SceneKraft" entry

4. **Test startup launch:**
   - Restart Windows
   - SceneKraft should start automatically
   - Wallpaper should appear if it was enabled before shutdown
   - Manager window should stay hidden if wallpaper exists

### Test 7: Configuration Persistence

1. **Select a wallpaper file**
2. **Enable it**
3. **Close the manager** (X button)
4. **Reopen manager:** `python app.py`
5. **Verify:**
   - Same wallpaper is still selected
   - Same startup checkbox state
   - File path is shown

### Test 8: Process Cleanup

1. **Open Task Manager** (Ctrl+Shift+Esc)
2. **Enable wallpaper** in SceneKraft
3. **Look in Task Manager** for Python processes
4. **Should see:**
   - One python process for manager (Tkinter)
   - One python process for wallpaper (pywebview)

5. **Click Disable Wallpaper**
6. **Check Task Manager** again
7. **Wallpaper process should terminate** within 1 second

### Test 9: Error Handling - Missing File

1. **Select a wallpaper file**
2. **Delete the file** from disk
3. **Click Enable**
4. **Observe:** Error message "The selected HTML file no longer exists."

### Test 10: Error Handling - Invalid Path

1. **Navigate to a folder** with spaces in the path
2. **Create an HTML file there**
3. **Select it and enable**
4. **Should work correctly** (paths with spaces handled)

### Test 11: Logging

1. **Check log file:** `~/.scenekraft/scenekraft.log`
2. **Verify it contains:**
   - Process start events
   - File path information
   - Wallpaper attachment success/failure
   - Any errors with full tracebacks

### Test 12: Multiple Monitors

1. **If you have multiple monitors:**
   - Enable wallpaper
   - Verify it covers **all** connected monitors
   - Check the virtual desktop dimensions in the log

---

## 5. PYINSTALLER COMPILATION

### Step 1: Install PyInstaller

```bash
pip install pyinstaller
```

### Step 2: Create PyInstaller Spec File

Create `scenekraft.spec`:

```python
# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules
import sys

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'webview',
        'webview.api',
        'tkinter',
        'winreg',
    ] + collect_submodules('webview'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SceneKraft',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',  # Optional: add your icon file
)
```

### Step 3: Build the Executable

```bash
pyinstaller scenekraft.spec
```

This creates `dist/SceneKraft.exe` (size ~80-120 MB with webview included).

### Step 4: Test the Executable

```cmd
dist\SceneKraft.exe
```

The manager UI should appear.

### Step 5: Create Windows Shortcut

1. Right-click `SceneKraft.exe`
2. Create Shortcut
3. Place on Desktop or Start Menu
4. Optionally edit properties to set icon

### Step 6: Distributable Package

The following files should be distributed together:
- `SceneKraft.exe` (main executable)
- Any required DLLs from the `dist` folder
- Optional: `icon.ico` (if customized)

Users only need to run `SceneKraft.exe`.

---

## 6. ARCHITECTURE OVERVIEW

### Process Model

```
┌─────────────────────────────────────────┐
│   Manager Process (Tkinter UI)          │
│  - File selection dialog                │
│  - Configuration management             │
│  - Windows startup registry             │
│  - Subprocess control                   │
│  - Status monitoring                    │
└──────────────┬──────────────────────────┘
               │
               │ subprocess.Popen()
               │ with --wallpaper-mode
               │
┌──────────────▼──────────────────────────┐
│  Wallpaper Process (pywebview)          │
│  - WebView2 window creation             │
│  - HTML/CSS/JavaScript rendering       │
│  - WorkerW attachment                   │
│  - Event loop (webview.start())         │
│  - HWND file-based IPC                  │
└─────────────────────────────────────────┘
```

### File Structure

```
~/.scenekraft/
├── config.json              # Configuration (wallpaper path, etc.)
├── scenekraft.log           # Application log
└── wallpaper_hwnd.txt       # HWND communication (temporary)
```

### Key Classes

**Config**
- `load()` - Load JSON config
- `save()` - Save JSON config
- `get_wallpaper_path()` - Get saved wallpaper with validation
- `set_wallpaper_path()` - Save wallpaper path

**Startup**
- `is_enabled()` - Check registry
- `set_enabled()` - Modify registry
- `_get_executable_path()` - Handle PyInstaller vs Python script

**WindowsAPI**
- `find_window()` - Find window by class/title
- `prepare_desktop()` - Send message to Progman
- `find_workerw()` - Enumerate and find WorkerW
- `get_virtual_screen_rect()` - Get multi-monitor bounds
- `attach_to_desktop()` - Complete attachment sequence

**WallpaperProcessManager**
- `start()` - Launch wallpaper subprocess
- `stop()` - Terminate subprocess with timeout
- `restart()` - Stop then start
- `is_running()` - Check if process alive
- `get_hwnd()` - Read HWND from file

**SceneKraftUI**
- `build_ui()` - Create Tkinter widgets
- `enable_wallpaper()` - Start wallpaper process
- `disable_wallpaper()` - Stop wallpaper process
- `monitor_wallpaper()` - Poll process status
- `on_close()` - Cleanup and exit

### Entry Point

The script checks `sys.argv`:
- No special args → Run manager UI (Tkinter)
- `--wallpaper-mode <path>` → Run wallpaper subprocess
- `--startup` → Run manager in hidden mode, auto-start if file exists

---

## 7. TROUBLESHOOTING

### Issue: Wallpaper doesn't appear

**Symptoms:** Status shows "Wallpaper enabled" but nothing on desktop

**Causes:**
1. WorkerW not found - desktop not initialized
2. WebView window created but not attached
3. Window style not set correctly

**Solution:**
1. Check `~/.scenekraft/scenekraft.log` for errors
2. Try again - Windows may need time to initialize
3. Restart Explorer: `taskkill /F /IM explorer.exe` then start explorer again
4. Reboot

### Issue: Process doesn't terminate

**Symptoms:** Wallpaper disabled but process still running in Task Manager

**Cause:** Process stuck in webview event loop

**Solution:**
1. Check log for errors
2. Use Task Manager to force kill if needed
3. Report issue with log contents

### Issue: WebView2 runtime error

**Symptoms:** Error about WebView2, edge or CEF not found

**Solution:**
1. Download WebView2 Evergreen Runtime from https://developer.microsoft.com/en-us/microsoft-edge/webview2/
2. Install it
3. Restart SceneKraft

### Issue: Startup doesn't work

**Symptoms:** App doesn't start when Windows boots

**Cause:** Registry entry missing or executable path wrong

**Solution:**
1. Check registry: `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`
2. Look for "SceneKraft" entry
3. Verify the command path is correct
4. Check `~/.scenekraft/scenekraft.log`
5. Re-enable startup checkbox

### Issue: "Access denied" when setting startup

**Symptoms:** Error when checking "Start with Windows"

**Cause:** Registry permissions, or running as different user

**Solution:**
1. Run as the user account you want startup for
2. Log out and log back in
3. Try again

### Issue: Paths with special characters break

**Symptoms:** Wallpaper doesn't load if path has Chinese characters, Unicode, etc.

**Solution:**
1. Already handled in new version (UTF-8 encoding throughout)
2. Check log to see exact path being used
3. Verify file exists at that exact path

---

## 8. CONFIGURATION FILE FORMAT

`~/.scenekraft/config.json`:

```json
{
  "wallpaper_path": "C:\\Users\\YourName\\Pictures\\wallpaper.html",
  "startup_enabled": false
}
```

**Notes:**
- `wallpaper_path`: Absolute path to selected HTML file (empty string if none selected)
- `startup_enabled`: Not currently used in manager (registry is source of truth), but reserved for future use

---

## 9. LOG FILE EXAMPLE

`~/.scenekraft/scenekraft.log`:

```
2024-01-15 10:30:45,123 - INFO - Wallpaper process started: C:\Users\User\Pictures\wallpaper.html
2024-01-15 10:30:45,234 - INFO - Loading wallpaper from: file:///C:/Users/User/Pictures/wallpaper.html
2024-01-15 10:30:46,500 - INFO - Webview window shown, getting HWND
2024-01-15 10:30:46,750 - INFO - Webview HWND: 2097152
2024-01-15 10:30:46,850 - INFO - Desktop prepared successfully
2024-01-15 10:30:47,100 - INFO - Found WorkerW: 2031784
2024-01-15 10:30:47,200 - INFO - Attaching wallpaper 2097152 to WorkerW 2031784
2024-01-15 10:30:47,300 - INFO - Wallpaper positioned at (0, 0) size (3840x2160)
2024-01-15 10:30:47,350 - INFO - Successfully attached to desktop
```

**Log levels:**
- `INFO` - Normal operation
- `WARNING` - Recoverable issues (e.g., failed to find HWND by title)
- `ERROR` - Significant failures (e.g., couldn't attach to desktop)
- `DEBUG` - Detailed diagnostic info (not shown to console by default)

---

## 10. KNOWN LIMITATIONS

1. **Windows only** - Uses Windows API calls, registry, WorkerW
2. **No animations during attachment** - Wallpaper may flicker slightly when enabling
3. **Desktop refresh on monitor change** - Wallpaper may need restart after monitor reconnection
4. **No per-monitor selection** - Same wallpaper on all monitors
5. **No scheduling** - Always manual enable/disable or startup

---

## 11. FUTURE ENHANCEMENTS

Possible improvements in v2.1+:
- [ ] Detect monitor hotplug and adjust wallpaper
- [ ] Pause wallpaper to save CPU
- [ ] Rotation between multiple HTML files
- [ ] Scheduled enable/disable times
- [ ] WebGL/animation performance monitoring
- [ ] Per-monitor wallpaper selection
- [ ] Theme selector (dark/light)
- [ ] Wallpaper preview window

---

## Migration from v1.x

If you're upgrading from the old version:

1. **Uninstall the old version** (if separate installation)
2. **Replace `app.py` with new version**
3. **Config should migrate automatically:**
   - Old `~/.scenekraft/wallpaper.txt` will be read
   - Settings will be saved to new `config.json`
   - Old text file is not deleted (safe to keep)

4. **Registry settings preserved:**
   - Startup entry remains valid
   - No need to re-enable startup

5. **Test thoroughly** before relying on it

---

## Support & Debugging

**For issues:**
1. Check `~/.scenekraft/scenekraft.log`
2. Check Windows Event Viewer for crashes
3. Verify WebView2 is installed
4. Try running in Python console mode for traceback: `python app.py 2>&1`

**For PyInstaller builds:**
- If it fails to start, run from command prompt to see error
- Check that all dependencies are included in `.spec` file
- Verify paths in your system

---
