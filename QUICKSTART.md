# SceneKraft 2.0 - Quick Start Guide

## Installation (30 seconds)

```bash
pip install pywebview
python app.py
```

Done! The manager window should appear.

## Basic Usage

1. **Select wallpaper:**
   - Click "BROWSE COMPUTER"
   - Pick an HTML file (or create one)

2. **Enable wallpaper:**
   - Click "ENABLE WALLPAPER"
   - Wait 2-3 seconds
   - Wallpaper appears on desktop

3. **Disable wallpaper:**
   - Click "DISABLE WALLPAPER"
   - Desktop returns to normal

4. **Windows startup:**
   - Check "Start SceneKraft with Windows"
   - Wallpaper will auto-enable on next boot

## Create Test Wallpaper

Save as `test.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            margin: 0;
            background: linear-gradient(135deg, #667eea, #764ba2);
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-family: Arial;
        }
    </style>
</head>
<body>
    <h1>My Custom Wallpaper</h1>
</body>
</html>
```

Then select it in SceneKraft.

## Troubleshooting

**Wallpaper doesn't appear?**
- Check: `C:\Users\YourName\.scenekraft\scenekraft.log`
- Restart Windows Explorer if needed
- Reboot computer

**WebView2 error?**
- Download: https://developer.microsoft.com/en-us/microsoft-edge/webview2/
- Install and restart SceneKraft

**Still issues?**
- Read full documentation: `MIGRATION.md`
- Check log file for errors

## Key Improvements Over v1

✅ **Two separate processes** - No event loop conflicts  
✅ **Reliable subprocess management** - Clean startup/shutdown  
✅ **Proper logging** - Errors saved to file  
✅ **Robust WorkerW detection** - Desktop attachment works reliably  
✅ **Better error messages** - Know what went wrong  
✅ **Multi-monitor support** - Wallpaper covers all displays  
✅ **PyInstaller ready** - Can be packaged as .exe  
✅ **Process cleanup** - No orphaned processes  

## Files

- `app.py` - Main application (single file)
- `~/.scenekraft/config.json` - Your settings
- `~/.scenekraft/scenekraft.log` - Application log

## Next Steps

- Read `MIGRATION.md` for full documentation
- Check troubleshooting section if issues
- Use `PYINSTALLER.md` to create .exe
