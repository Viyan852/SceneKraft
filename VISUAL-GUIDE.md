# 🎬 SceneKraft v2.0 - Visual Step-by-Step Guide

## STEP 1: Your Folder (What You Have)

```
Your SceneKraft Folder
├── 📄 app.py                  ← NEW v2.0 version
├── 🎨 favicon.ico             ← Icon for .exe
├── ⚙️  SceneKraft.spec        ← PyInstaller config
├── 📋 requirements.txt        ← Dependencies (only pywebview)
├── 📖 README.md
├── 📜 LICENSE
└── 🎬 wallpaper/              ← Example HTML wallpaper
```

---

## STEP 2: Test Locally (5 minutes)

### 2.1 Open Command Prompt

```
cd C:\Users\YourName\path\to\SceneKraft
```

### 2.2 Install PyInstaller

```bash
pip install pyinstaller
```

```
Output:
Successfully installed pyinstaller-6.x.x
```

### 2.3 Clean Old Builds

```bash
rmdir /s /q build dist
```

```
Output:
(Removes old build files)
```

### 2.4 Build

```bash
pyinstaller SceneKraft.spec
```

```
Output:
[lots of output...]
successfully built 'dist\SceneKraft.exe'
```

### 2.5 Test Run

```bash
dist\SceneKraft.exe
```

```
✅ Window opens
✅ Can click "Browse"
✅ Can select HTML file
✅ Can click "Enable"
✅ Wallpaper appears
✅ Icon shows in taskbar
```

---

## STEP 3: GitHub Setup (One Time - 10 minutes)

### 3.1 Create GitHub Repository

**Go to:** https://github.com/new

```
Repository name: SceneKraft
Description: HTML/CSS/JavaScript Wallpaper Engine for Windows
Public: ✓
Add LICENSE: ✓
Click "Create repository"
```

**Result:** New repo at `https://github.com/YOU/SceneKraft`

### 3.2 Copy Repository URL

On GitHub, click green "Code" button:
```
https://github.com/YOUR-USERNAME/SceneKraft.git
```

Copy this URL.

### 3.3 Initialize Git in Your Folder

**In Command Prompt:**

```bash
cd your-scenekraft-folder
git init
```

```
Output:
Initialized empty Git repository in C:\...\.git\
```

### 3.4 Add Remote

```bash
git remote add origin https://github.com/YOUR-USERNAME/SceneKraft.git
```

Verify:
```bash
git remote -v
```

```
Output:
origin  https://github.com/YOUR-USERNAME/SceneKraft.git (fetch)
origin  https://github.com/YOUR-USERNAME/SceneKraft.git (push)
```

### 3.5 Push to GitHub

```bash
git add .
git commit -m "Initial commit: SceneKraft v2.0"
git branch -M main
git push -u origin main
```

```
Output:
...
* [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

**Go to GitHub** → You should see all your files there! ✅

---

## STEP 4: Add GitHub Actions (5 minutes)

### 4.1 Create Workflows Folder

**In your folder, create:**
```
.github/
└── workflows/
    ├── build-windows.yml
    └── build-macos.yml
```

### 4.2 Add Windows Workflow

**Create file:** `.github/workflows/build-windows.yml`

Copy contents from the `build-windows.yml` file provided.

### 4.3 Add macOS Workflow

**Create file:** `.github/workflows/build-macos.yml`

Copy contents from the `build-macos.yml` file provided.

### 4.4 Commit Workflows

```bash
git add .github/
git commit -m "Add GitHub Actions workflows"
git push origin main
```

```
Output:
✓ Workflows pushed
```

**Go to GitHub:**
- Actions tab
- You should see both workflows listed! ✅

---

## STEP 5: Make a Release (5 minutes)

### 5.1 Create Version Tag

```bash
git tag -a v2.0 -m "SceneKraft v2.0: Complete rewrite with multi-process architecture"
git push origin v2.0
```

```
Output:
To https://github.com/YOUR-USERNAME/SceneKraft.git
 * [new tag]         v2.0 -> v2.0
```

### 5.2 GitHub Actions Starts Building

**Go to:** https://github.com/YOUR-USERNAME/SceneKraft/actions

```
You see:
┌─────────────────────────────┐
│ Build SceneKraft (Windows)  │ 🟡 In Progress...
└─────────────────────────────┘

┌─────────────────────────────┐
│ Build SceneKraft (macOS)    │ 🟡 In Progress...
└─────────────────────────────┘
```

**Wait ~15 minutes...**

```
After 15 minutes:
┌─────────────────────────────┐
│ Build SceneKraft (Windows)  │ ✅ Completed
└─────────────────────────────┘

┌─────────────────────────────┐
│ Build SceneKraft (macOS)    │ ✅ Completed
└─────────────────────────────┘
```

### 5.3 GitHub Creates Release

**Go to:** https://github.com/YOUR-USERNAME/SceneKraft/releases

```
You see:
v2.0
├── SceneKraft-Windows-x64.zip  (120 MB) ✅
├── SceneKraft-macOS-arm64.dmg  (120 MB) ✅
└── Release notes
```

---

## STEP 6: Verify & Test (5 minutes)

### 6.1 Download Windows Version

**From GitHub Releases:**
- Click `SceneKraft-Windows-x64.zip`
- Extract
- Run `SceneKraft.exe`

```
✅ App launches
✅ Everything works
✅ Icon visible
```

### 6.2 Download macOS Version (if available)

**From GitHub Releases:**
- Click `SceneKraft-macOS-arm64.dmg`
- Mount DMG
- Drag to Applications
- Run

```
✅ App launches on macOS
```

### 6.3 Share with Users

```
GitHub Releases URL:
https://github.com/YOUR-USERNAME/SceneKraft/releases

Users download from here:
- Windows: SceneKraft-Windows-x64.zip
- macOS: SceneKraft-macOS-arm64.dmg
```

---

## COMPLETE FOLDER STRUCTURE AFTER SETUP

```
SceneKraft/
│
├── .github/
│   └── workflows/
│       ├── build-windows.yml      ✅ Automated build
│       └── build-macos.yml        ✅ Automated build
│
├── build/                         (temp, auto-created)
│   └── (PyInstaller artifacts)
│
├── dist/                          (temp, auto-created)
│   ├── SceneKraft.exe            ← Your Windows app
│   └── (other files)
│
├── .git/                          (hidden, git files)
├── .gitignore                     ✅ Ignore build artifacts
├── app.py                         ✅ Main app (v2.0)
├── favicon.ico                    ✅ Icon
├── LICENSE                        ✅ MIT License
├── README.md                      ✅ Documentation
├── requirements.txt               ✅ Dependencies
├── SceneKraft.spec                ✅ Build config
└── wallpaper/                     ✅ Example wallpaper
```

---

## WORKFLOW DIAGRAM

```
┌───────────────────────────────────────────┐
│ 1. You Edit app.py                        │
│    • Add features                         │
│    • Fix bugs                             │
│    • Test locally                         │
└──────────────┬────────────────────────────┘
               │
               ▼
┌───────────────────────────────────────────┐
│ 2. Commit to Git                          │
│    git add .                              │
│    git commit -m "..."                    │
│    git push origin main                   │
└──────────────┬────────────────────────────┘
               │
               ▼
┌───────────────────────────────────────────┐
│ 3. Create Version Tag                     │
│    git tag -a v2.0.1 -m "..."             │
│    git push origin v2.0.1                 │
└──────────────┬────────────────────────────┘
               │
        ┌──────┴──────┐
        │             │
        ▼             ▼
   ┌────────┐    ┌────────┐
   │Windows │    │ macOS  │
   │ Build  │    │ Build  │
   │(15min) │    │(15min) │
   └────────┘    └────────┘
        │             │
        └──────┬──────┘
               │
               ▼
    ┌─────────────────────┐
    │ GitHub Release      │
    │ Both files attached │
    │ Ready for download  │
    └─────────────────────┘
```

---

## TYPICAL RELEASE FLOW (After First Setup)

### Every Time You Want to Release:

```bash
# 1. Make changes
(edit app.py)

# 2. Test locally (2 min)
pyinstaller SceneKraft.spec && dist\SceneKraft.exe

# 3. Commit changes (2 min)
git add .
git commit -m "v2.0.1: Added feature X"
git push origin main

# 4. Create release (1 min)
git tag -a v2.0.1 -m "SceneKraft v2.0.1"
git push origin v2.0.1

# 5. Wait for builds (15-20 min)
# (Check https://github.com/YOU/SceneKraft/actions)

# 6. Download & test (5 min)
# Done! 🎉
```

**Total: ~25 minutes per release**

---

## GITHUB URLS TO BOOKMARK

```
Main Repository:
https://github.com/YOUR-USERNAME/SceneKraft

Build Status (Actions):
https://github.com/YOUR-USERNAME/SceneKraft/actions

Downloads (Releases):
https://github.com/YOUR-USERNAME/SceneKraft/releases

Settings:
https://github.com/YOUR-USERNAME/SceneKraft/settings
```

---

## SUCCESS INDICATORS

### ✅ Local Build Works
```bash
pyinstaller SceneKraft.spec
dist\SceneKraft.exe launches perfectly
```

### ✅ GitHub Setup Works
```
https://github.com/YOU/SceneKraft
All files visible
```

### ✅ Workflows Exist
```
Actions tab shows:
- build-windows.yml
- build-macos.yml
```

### ✅ First Release Works
```
https://github.com/YOU/SceneKraft/releases/tag/v2.0
Shows both .exe.zip and .dmg files
```

### ✅ Builds Completed
```
Both builds show green ✅
Both downloads available
```

---

## COMMON MISTAKES & FIXES

### ❌ "No releases yet"
**Problem:** You pushed commit but not the tag

**Fix:**
```bash
git tag -a v2.0 -m "..."
git push origin v2.0  # ← Push the TAG!
```

### ❌ "Build still running after 30 min"
**Problem:** Something failed in build

**Fix:**
1. Go to Actions
2. Click the failed job
3. Read the error log
4. Fix locally: `pyinstaller SceneKraft.spec`
5. Retag: `git tag -d v2.0 && git push origin :v2.0`
6. Create new tag: `git tag -a v2.0 -m "..." && git push origin v2.0`

### ❌ "Authentication failed"
**Problem:** GitHub token issue

**Fix:**
1. Generate token: https://github.com/settings/tokens
2. Check "repo" permissions
3. Use token as password when prompted

### ❌ "pywebview not found"
**Problem:** requirements.txt wrong or not pushed

**Fix:**
1. Check `requirements.txt` has `pywebview`
2. Test locally: `pip install -r requirements.txt`
3. Commit: `git add requirements.txt && git commit && git push`
4. Retag and push

---

## 🎉 YOU'RE DONE!

You now have a professional, automated release pipeline:

✅ **Code** → `.github/workflows/` → **Builds** → **Releases**

Every tag you push = automatic release for both Windows and macOS!

**Congratulations!** 🚀
