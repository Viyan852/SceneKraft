import os
import sys
import time
import ctypes
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import winreg

import webview


# ============================================================
# SCENEKRAFT
# Single-file HTML wallpaper engine for Windows 10
# ============================================================

APP_NAME = "SceneKraft"
WALLPAPER_TITLE = "SceneKraft Wallpaper"

CONFIG_DIR = os.path.join(
    os.path.expanduser("~"),
    ".scenekraft"
)

CONFIG_FILE = os.path.join(
    CONFIG_DIR,
    "wallpaper.txt"
)

STARTUP_NAME = "SceneKraft"

os.makedirs(CONFIG_DIR, exist_ok=True)


# ============================================================
# STATE
# ============================================================

selected_file = ""
wallpaper_window = None
wallpaper_running = False

webview_ready = threading.Event()
stop_requested = False


# ============================================================
# CONFIG
# ============================================================

def save_wallpaper(path):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(path)
    except Exception:
        pass


def load_wallpaper():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                path = f.read().strip()

            if os.path.isfile(path):
                return path

    except Exception:
        pass

    return ""


# ============================================================
# WINDOWS STARTUP
# ============================================================

def is_startup_enabled():

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ
        )

        try:
            winreg.QueryValueEx(
                key,
                STARTUP_NAME
            )

            winreg.CloseKey(key)
            return True

        except FileNotFoundError:

            winreg.CloseKey(key)
            return False

    except Exception:
        return False


def set_startup(enabled):

    try:

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )

        if enabled:

            python = sys.executable

            # Hide console when possible
            if python.lower().endswith("python.exe"):
                python = python[:-10] + "pythonw.exe"

            script = os.path.abspath(__file__)

            command = f'"{python}" "{script}" --startup'

            winreg.SetValueEx(
                key,
                STARTUP_NAME,
                0,
                winreg.REG_SZ,
                command
            )

        else:

            try:
                winreg.DeleteValue(
                    key,
                    STARTUP_NAME
                )
            except FileNotFoundError:
                pass

        winreg.CloseKey(key)

        return True

    except Exception as e:

        messagebox.showerror(
            "SceneKraft",
            "Could not modify Windows startup:\n\n"
            + str(e)
        )

        return False


# ============================================================
# WINDOWS DESKTOP / WORKERW
# ============================================================

user32 = ctypes.windll.user32

EnumWindowsProc = ctypes.WINFUNCTYPE(
    ctypes.c_bool,
    ctypes.c_void_p,
    ctypes.c_void_p
)


def prepare_desktop():

    progman = user32.FindWindowW(
        "Progman",
        None
    )

    if not progman:
        return

    result = ctypes.c_ulong()

    user32.SendMessageTimeoutW(
        progman,
        0x052C,
        0,
        0,
        0,
        1000,
        ctypes.byref(result)
    )


def find_workerw():

    workerw = None

    def callback(hwnd, lparam):

        nonlocal workerw

        shell = user32.FindWindowExW(
            hwnd,
            0,
            "SHELLDLL_DefView",
            None
        )

        if shell:

            workerw = user32.FindWindowExW(
                0,
                hwnd,
                "WorkerW",
                None
            )

        return True

    user32.EnumWindows(
        EnumWindowsProc(callback),
        0
    )

    return workerw


def attach_to_desktop(hwnd):

    prepare_desktop()

    time.sleep(0.5)

    workerw = find_workerw()

    if not workerw:
        return False

    GWL_STYLE = -16
    WS_CHILD = 0x40000000

    style = user32.GetWindowLongW(
        hwnd,
        GWL_STYLE
    )

    user32.SetWindowLongW(
        hwnd,
        GWL_STYLE,
        style | WS_CHILD
    )

    user32.SetParent(
        hwnd,
        workerw
    )

    # Windows virtual desktop
    SM_XVIRTUALSCREEN = 76
    SM_YVIRTUALSCREEN = 77
    SM_CXVIRTUALSCREEN = 78
    SM_CYVIRTUALSCREEN = 79

    x = user32.GetSystemMetrics(
        SM_XVIRTUALSCREEN
    )

    y = user32.GetSystemMetrics(
        SM_YVIRTUALSCREEN
    )

    width = user32.GetSystemMetrics(
        SM_CXVIRTUALSCREEN
    )

    height = user32.GetSystemMetrics(
        SM_CYVIRTUALSCREEN
    )

    user32.SetWindowPos(
        hwnd,
        0,
        x,
        y,
        width,
        height,
        0x0040
    )

    return True


# ============================================================
# WEBVIEW
#
# IMPORTANT:
# webview.start() is called on the MAIN THREAD.
# ============================================================

def create_wallpaper():

    global wallpaper_window

    if not selected_file:
        return

    html_path = os.path.abspath(
        selected_file
    )

    html_url = (
        "file:///"
        + html_path.replace(
            "\\",
            "/"
        )
    )

    wallpaper_window = webview.create_window(

        WALLPAPER_TITLE,

        html_url,

        fullscreen=True,

        frameless=True,

        resizable=False,

        easy_drag=False,

        text_select=False,

        zoomable=False,

        confirm_close=False
    )


def webview_started():

    """
    Called by pywebview after the GUI loop starts.
    """

    global wallpaper_running

    wallpaper_running = True

    webview_ready.set()

    # Find native HWND after WebView exists
    threading.Thread(
        target=attach_wallpaper,
        daemon=True
    ).start()


def attach_wallpaper():

    global wallpaper_running

    time.sleep(1.0)

    hwnd = user32.FindWindowW(
        None,
        WALLPAPER_TITLE
    )

    if not hwnd:

        wallpaper_running = False

        root.after(
            0,
            lambda: set_status(
                "● Wallpaper window not found",
                "#f87171"
            )
        )

        return

    success = attach_to_desktop(hwnd)

    if success:

        root.after(
            0,
            lambda: set_status(
                "● Wallpaper enabled",
                "#4ade80"
            )
        )

    else:

        root.after(
            0,
            lambda: set_status(
                "● Wallpaper running",
                "#facc15"
            )
        )


def close_wallpaper():

    global wallpaper_running

    if wallpaper_window:

        try:
            wallpaper_window.destroy()
        except Exception:
            pass

    wallpaper_running = False


# ============================================================
# WALLPAPER THREAD CONTROL
# ============================================================

def enable_wallpaper():

    global selected_file

    if wallpaper_running:
        return

    if not selected_file:

        messagebox.showwarning(
            "SceneKraft",
            "Select an HTML wallpaper first."
        )

        return

    if not os.path.isfile(selected_file):

        messagebox.showerror(
            "SceneKraft",
            "The selected HTML file no longer exists."
        )

        return

    save_wallpaper(selected_file)

    set_status(
        "● Loading wallpaper...",
        "#facc15"
    )

    enable_button.config(
        bg="#16a34a"
    )

    # WebView has to be running on main thread.
    # We signal the main-loop controller.
    start_webview()


def start_webview():

    global wallpaper_window

    if wallpaper_window:
        return

    create_wallpaper()

    # IMPORTANT:
    # This must execute on the main thread.
    #
    # Since Tkinter also needs its own event loop, the manager
    # uses a small control window and pywebview owns the main
    # GUI loop once the wallpaper is enabled.
    #
    # The manager remains available through its window callbacks.

    webview.start(
        func=webview_started,
        debug=False
    )


# ============================================================
# DISABLE
# ============================================================

def disable_wallpaper():

    global wallpaper_window
    global wallpaper_running

    close_wallpaper()

    wallpaper_window = None
    wallpaper_running = False

    set_status(
        "● Wallpaper disabled",
        "#f87171"
    )

    enable_button.config(
        bg="#263044"
    )


# ============================================================
# FILE BROWSER
# ============================================================

def browse_wallpaper():

    global selected_file

    path = filedialog.askopenfilename(

        title="Select HTML Wallpaper",

        initialdir=os.path.expanduser("~"),

        filetypes=[
            (
                "HTML files",
                "*.html *.htm"
            ),
            (
                "All files",
                "*.*"
            )
        ]
    )

    if not path:
        return

    selected_file = os.path.abspath(path)

    save_wallpaper(selected_file)

    show_file()

    set_status(
        "● Wallpaper selected",
        "#60a5fa"
    )


def show_file():

    if selected_file:

        filename_label.config(
            text=os.path.basename(
                selected_file
            ),
            fg="#ffffff"
        )

        path_label.config(
            text=selected_file,
            fg="#64748b"
        )

        browse_button.config(
            text="📁   CHANGE WALLPAPER"
        )

    else:

        filename_label.config(
            text="No wallpaper selected",
            fg="#64748b"
        )

        path_label.config(
            text="Choose an HTML file from your computer.",
            fg="#64748b"
        )


# ============================================================
# STARTUP
# ============================================================

def startup_changed():

    enabled = startup_var.get()

    if set_startup(enabled):

        startup_status.config(
            text=(
                "Enabled"
                if enabled
                else "Disabled"
            ),
            fg=(
                "#4ade80"
                if enabled
                else "#64748b"
            )
        )


# ============================================================
# STATUS
# ============================================================

def set_status(text, color):

    try:

        status_label.config(
            text=text,
            fg=color
        )

    except Exception:
        pass


# ============================================================
# BUTTON
# ============================================================

def button(
    parent,
    text,
    command,
    bg,
    active
):

    return tk.Button(

        parent,

        text=text,

        command=command,

        font=(
            "Segoe UI",
            10,
            "bold"
        ),

        bg=bg,

        fg="white",

        activebackground=active,

        activeforeground="white",

        relief="flat",

        bd=0,

        cursor="hand2",

        padx=23,

        pady=11
    )


# ============================================================
# MAIN UI
# ============================================================

root = tk.Tk()

root.title(APP_NAME)

root.geometry(
    "760x560"
)

root.resizable(
    False,
    False
)

root.configure(
    bg="#080c16"
)


# Center
root.update_idletasks()

sw = root.winfo_screenwidth()
sh = root.winfo_screenheight()

root.geometry(
    f"760x560+"
    f"{(sw-760)//2}+"
    f"{(sh-560)//2}"
)


# ============================================================
# HEADER
# ============================================================

header = tk.Frame(
    root,
    bg="#101827",
    height=125
)

header.pack(
    fill="x"
)

header.pack_propagate(False)


tk.Label(
    header,
    text="SCENEKRAFT",
    font=(
        "Segoe UI",
        10,
        "bold"
    ),
    bg="#101827",
    fg="#3b82f6"
).pack(
    pady=(20, 0)
)


tk.Label(
    header,
    text="HTML Wallpaper Engine",
    font=(
        "Segoe UI",
        25,
        "bold"
    ),
    bg="#101827",
    fg="white"
).pack()


tk.Label(
    header,
    text="HTML  •  CSS  •  JavaScript  •  WebView2",
    font=(
        "Segoe UI",
        9
    ),
    bg="#101827",
    fg="#64748b"
).pack()


# ============================================================
# CONTENT
# ============================================================

content = tk.Frame(
    root,
    bg="#080c16"
)

content.pack(
    fill="both",
    expand=True,
    padx=48,
    pady=28
)


tk.Label(
    content,
    text="WALLPAPER",
    font=(
        "Segoe UI",
        9,
        "bold"
    ),
    bg="#080c16",
    fg="#64748b"
).pack(
    anchor="w"
)


# ============================================================
# FILE CARD
# ============================================================

file_card = tk.Frame(
    content,
    bg="#111827",
    height=82
)

file_card.pack(
    fill="x",
    pady=(8, 13)
)

file_card.pack_propagate(False)


filename_label = tk.Label(
    file_card,
    text="No wallpaper selected",
    font=(
        "Segoe UI",
        11,
        "bold"
    ),
    bg="#111827",
    fg="#64748b",
    anchor="w"
)

filename_label.pack(
    padx=18,
    pady=(14, 0),
    anchor="w"
)


path_label = tk.Label(
    file_card,
    text="Choose an HTML file from your computer.",
    font=(
        "Segoe UI",
        8
    ),
    bg="#111827",
    fg="#64748b",
    anchor="w"
)

path_label.pack(
    padx=18,
    anchor="w"
)


browse_button = button(
    content,
    "📁   BROWSE COMPUTER",
    browse_wallpaper,
    "#2563eb",
    "#1d4ed8"
)

browse_button.pack(
    anchor="w"
)


# ============================================================
# CONTROL
# ============================================================

control_card = tk.Frame(
    content,
    bg="#101827"
)

control_card.pack(
    fill="x",
    pady=24
)


tk.Label(
    control_card,
    text="WALLPAPER CONTROL",
    font=(
        "Segoe UI",
        9,
        "bold"
    ),
    bg="#101827",
    fg="#64748b"
).pack(
    anchor="w",
    padx=20,
    pady=(14, 9)
)


controls = tk.Frame(
    control_card,
    bg="#101827"
)

controls.pack(
    pady=(0, 16)
)


enable_button = button(
    controls,
    "✓   ENABLE WALLPAPER",
    enable_wallpaper,
    "#16a34a",
    "#15803d"
)

enable_button.pack(
    side="left",
    padx=5
)


disable_button = button(
    controls,
    "×   DISABLE WALLPAPER",
    disable_wallpaper,
    "#263044",
    "#334155"
)

disable_button.pack(
    side="left",
    padx=5
)


# ============================================================
# STARTUP
# ============================================================

startup_var = tk.BooleanVar(
    value=is_startup_enabled()
)


startup_card = tk.Frame(
    content,
    bg="#111827"
)

startup_card.pack(
    fill="x"
)


tk.Checkbutton(
    startup_card,

    text="Start SceneKraft with Windows",

    variable=startup_var,

    command=startup_changed,

    font=(
        "Segoe UI",
        10
    ),

    bg="#111827",

    fg="white",

    activebackground="#111827",

    activeforeground="white",

    selectcolor="#111827",

    cursor="hand2"
).pack(
    side="left",
    padx=16,
    pady=13
)


startup_status = tk.Label(
    startup_card,

    text=(
        "Enabled"
        if is_startup_enabled()
        else "Disabled"
    ),

    font=(
        "Segoe UI",
        9,
        "bold"
    ),

    bg="#111827",

    fg=(
        "#4ade80"
        if is_startup_enabled()
        else "#64748b"
    )
)

startup_status.pack(
    side="right",
    padx=16
)


# ============================================================
# STATUS
# ============================================================

status_label = tk.Label(
    content,

    text="● Wallpaper disabled",

    font=(
        "Segoe UI",
        9,
        "bold"
    ),

    bg="#080c16",

    fg="#f87171"
)

status_label.pack(
    pady=13
)


# ============================================================
# FOOTER
# ============================================================

tk.Label(
    root,
    text="SceneKraft  •  User mode  •  No administrator permission required",
    font=(
        "Segoe UI",
        8
    ),
    bg="#080c16",
    fg="#334155"
).pack(
    pady=(0, 14)
)


# ============================================================
# RESTORE
# ============================================================

selected_file = load_wallpaper()

show_file()


# ============================================================
# STARTUP MODE
# ============================================================

if "--startup" in sys.argv:

    root.withdraw()

    if selected_file and os.path.isfile(selected_file):

        # Give Windows Explorer time to initialize
        root.after(
            3000,
            enable_wallpaper
        )

    else:

        root.deiconify()


# ============================================================
# CLOSE
# ============================================================

def close_application():

    try:
        disable_wallpaper()
    except Exception:
        pass

    root.destroy()


root.protocol(
    "WM_DELETE_WINDOW",
    close_application
)


# ============================================================
# MAIN TKINTER LOOP
# ============================================================

root.mainloop()
