#!/usr/bin/env python3
"""
SceneKraft - HTML/CSS/JavaScript Wallpaper Engine for Windows

Install:
    python -m pip install -U pywebview pyinstaller

Run:
    python app.py

Build:
    python -m PyInstaller --clean --noconfirm SceneKraft.spec
"""

import argparse
import ctypes
import json
import logging
import os
import subprocess
import sys
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
import winreg


# ============================================================
# CONFIGURATION
# ============================================================

APP_NAME = "SceneKraft"
APP_VERSION = "3.0"

CONFIG_DIR = Path.home() / ".scenekraft"
CONFIG_FILE = CONFIG_DIR / "config.json"
LOG_FILE = CONFIG_DIR / "scenekraft.log"
HWND_FILE = CONFIG_DIR / "wallpaper_hwnd.txt"

STARTUP_NAME = "SceneKraft"
WALLPAPER_TITLE = "SceneKraft Wallpaper"

WALLPAPER_STOP_TIMEOUT = 5

CONFIG_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(APP_NAME)


# ============================================================
# CONFIGURATION MANAGEMENT
# ============================================================

class Config:
    DEFAULT = {
        "wallpaper_path": "",
    }

    @staticmethod
    def load():
        try:
            if not CONFIG_FILE.exists():
                return dict(Config.DEFAULT)

            with CONFIG_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                return dict(Config.DEFAULT)

            config = dict(Config.DEFAULT)
            config.update(data)

            return config

        except Exception:
            logger.exception("Failed to load configuration")
            return dict(Config.DEFAULT)

    @staticmethod
    def save(data):
        try:
            with CONFIG_FILE.open("w", encoding="utf-8") as f:
                json.dump(
                    data,
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

            return True

        except Exception:
            logger.exception("Failed to save configuration")
            return False

    @staticmethod
    def get_wallpaper_path():
        path = Config.load().get(
            "wallpaper_path",
            "",
        )

        if path and os.path.isfile(path):
            return os.path.abspath(path)

        return ""

    @staticmethod
    def set_wallpaper_path(path):
        config = Config.load()

        config["wallpaper_path"] = (
            os.path.abspath(path)
            if path
            else ""
        )

        return Config.save(config)


# ============================================================
# WINDOWS STARTUP
# ============================================================

class Startup:
    REG_PATH = (
        r"Software\Microsoft\Windows\CurrentVersion\Run"
    )

    @staticmethod
    def is_enabled():
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                Startup.REG_PATH,
                0,
                winreg.KEY_READ,
            ) as key:

                value, _ = winreg.QueryValueEx(
                    key,
                    STARTUP_NAME,
                )

                return bool(value)

        except FileNotFoundError:
            return False

        except Exception:
            logger.exception(
                "Failed to check startup status"
            )

            return False

    @staticmethod
    def get_command():
        """
        Return a valid Windows startup command.
        """

        # PyInstaller executable
        if getattr(sys, "frozen", False):
            return f'"{sys.executable}" --startup'

        # Normal Python execution
        python_exe = sys.executable

        # Prefer pythonw so no console appears at startup.
        if python_exe.lower().endswith("python.exe"):
            pythonw = (
                python_exe[:-len("python.exe")]
                + "pythonw.exe"
            )

            if os.path.isfile(pythonw):
                python_exe = pythonw

        script = os.path.abspath(__file__)

        return (
            f'"{python_exe}" '
            f'"{script}" '
            f'--startup'
        )

    @staticmethod
    def set_enabled(enabled):
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                Startup.REG_PATH,
                0,
                winreg.KEY_SET_VALUE,
            ) as key:

                if enabled:
                    command = Startup.get_command()

                    winreg.SetValueEx(
                        key,
                        STARTUP_NAME,
                        0,
                        winreg.REG_SZ,
                        command,
                    )

                    logger.info(
                        "Windows startup enabled"
                    )

                    logger.info(
                        "Startup command: %s",
                        command,
                    )

                else:
                    try:
                        winreg.DeleteValue(
                            key,
                            STARTUP_NAME,
                        )

                    except FileNotFoundError:
                        pass

                    logger.info(
                        "Windows startup disabled"
                    )

            return True

        except Exception:
            logger.exception(
                "Failed to modify Windows startup"
            )

            return False


# ============================================================
# WINDOWS API
# ============================================================

class WindowsAPI:
    user32 = ctypes.WinDLL(
        "user32",
        use_last_error=True,
    )

    GWL_STYLE = -16

    WS_CHILD = 0x40000000
    WS_POPUP = 0x80000000

    SWP_NOZORDER = 0x0004
    SWP_NOACTIVATE = 0x0010
    SWP_SHOWWINDOW = 0x0040

    SM_XVIRTUALSCREEN = 76
    SM_YVIRTUALSCREEN = 77
    SM_CXVIRTUALSCREEN = 78
    SM_CYVIRTUALSCREEN = 79

    WNDENUMPROC = ctypes.WINFUNCTYPE(
        ctypes.c_bool,
        ctypes.c_void_p,
        ctypes.c_void_p,
    )

    @staticmethod
    def find_window(
        class_name=None,
        title=None,
    ):
        try:
            hwnd = WindowsAPI.user32.FindWindowW(
                class_name,
                title,
            )

            return hwnd if hwnd else None

        except Exception:
            logger.exception(
                "FindWindowW failed"
            )

            return None

    @staticmethod
    def find_window_by_title(
        title,
        timeout=10,
    ):
        logger.info(
            "Searching for native window: %s",
            title,
        )

        deadline = time.time() + timeout

        while time.time() < deadline:
            hwnd = WindowsAPI.find_window(
                None,
                title,
            )

            if hwnd:
                logger.info(
                    "Found HWND=%s",
                    hwnd,
                )

                return hwnd

            time.sleep(0.1)

        logger.error(
            "Window not found: %s",
            title,
        )

        return None

    @staticmethod
    def prepare_desktop():
        """
        Ask Explorer to create the WorkerW desktop window.

        0x052C is the undocumented Progman message
        commonly used by wallpaper applications.
        """

        progman = WindowsAPI.find_window(
            "Progman",
            None,
        )

        if not progman:
            logger.error(
                "Progman window not found"
            )

            return False

        result = ctypes.c_ulong()

        try:
            ret = (
                WindowsAPI.user32
                .SendMessageTimeoutW(
                    progman,
                    0x052C,
                    0,
                    0,
                    0,
                    1000,
                    ctypes.byref(result),
                )
            )

            if ret:
                logger.info(
                    "Explorer desktop prepared"
                )

            else:
                logger.warning(
                    "SendMessageTimeoutW failed"
                )

            time.sleep(0.5)

            return True

        except Exception:
            logger.exception(
                "Failed to prepare desktop"
            )

            return False

    @staticmethod
    def find_workerw(timeout=5):
        """
        Find WorkerW behind SHELLDLL_DefView.
        """

        deadline = time.time() + timeout

        while time.time() < deadline:
            workerw = None

            def callback(hwnd, lparam):
                nonlocal workerw

                try:
                    shell_view = (
                        WindowsAPI.user32
                        .FindWindowExW(
                            hwnd,
                            0,
                            "SHELLDLL_DefView",
                            None,
                        )
                    )

                    if shell_view:
                        workerw = (
                            WindowsAPI.user32
                            .FindWindowExW(
                                0,
                                hwnd,
                                "WorkerW",
                                None,
                            )
                        )

                        if workerw:
                            return False

                except Exception:
                    logger.exception(
                        "WorkerW enumeration error"
                    )

                return True

            try:
                callback_object = (
                    WindowsAPI.WNDENUMPROC(
                        callback
                    )
                )

                WindowsAPI.user32.EnumWindows(
                    callback_object,
                    0,
                )

            except Exception:
                logger.exception(
                    "EnumWindows failed"
                )

            if workerw:
                logger.info(
                    "Found WorkerW HWND=%s",
                    workerw,
                )

                return workerw

            time.sleep(0.1)

        logger.error(
            "WorkerW was not found"
        )

        return None

    @staticmethod
    def get_virtual_screen():
        try:
            x = WindowsAPI.user32.GetSystemMetrics(
                WindowsAPI.SM_XVIRTUALSCREEN
            )

            y = WindowsAPI.user32.GetSystemMetrics(
                WindowsAPI.SM_YVIRTUALSCREEN
            )

            width = WindowsAPI.user32.GetSystemMetrics(
                WindowsAPI.SM_CXVIRTUALSCREEN
            )

            height = WindowsAPI.user32.GetSystemMetrics(
                WindowsAPI.SM_CYVIRTUALSCREEN
            )

            if width <= 0 or height <= 0:
                raise RuntimeError(
                    "Invalid virtual screen size"
                )

            return x, y, width, height

        except Exception:
            logger.exception(
                "Failed to get virtual screen size"
            )

            return (
                0,
                0,
                1920,
                1080,
            )

    @staticmethod
    def attach_to_desktop(hwnd):
        """
        Attach the WebView window to Explorer's WorkerW.
        """

        if not hwnd:
            logger.error(
                "Invalid wallpaper HWND"
            )

            return False

        if not WindowsAPI.prepare_desktop():
            return False

        workerw = WindowsAPI.find_workerw()

        if not workerw:
            return False

        logger.info(
            "Attaching HWND=%s to WorkerW=%s",
            hwnd,
            workerw,
        )

        try:
            style = (
                WindowsAPI.user32
                .GetWindowLongW(
                    hwnd,
                    WindowsAPI.GWL_STYLE,
                )
            )

            new_style = (
                (style | WindowsAPI.WS_CHILD)
                & ~WindowsAPI.WS_POPUP
            )

            WindowsAPI.user32.SetWindowLongW(
                hwnd,
                WindowsAPI.GWL_STYLE,
                new_style,
            )

            WindowsAPI.user32.SetParent(
                hwnd,
                workerw,
            )

            _, _, width, height = (
                WindowsAPI.get_virtual_screen()
            )

            result = (
                WindowsAPI.user32.SetWindowPos(
                    hwnd,
                    0,
                    0,
                    0,
                    width,
                    height,
                    (
                        WindowsAPI.SWP_NOZORDER
                        | WindowsAPI.SWP_NOACTIVATE
                        | WindowsAPI.SWP_SHOWWINDOW
                    ),
                )
            )

            if not result:
                error = ctypes.get_last_error()

                logger.error(
                    "SetWindowPos failed: %s",
                    error,
                )

                return False

            WindowsAPI.user32.ShowWindow(
                hwnd,
                5,
            )

            WindowsAPI.user32.UpdateWindow(
                hwnd
            )

            logger.info(
                "Wallpaper successfully attached"
            )

            return True

        except Exception:
            logger.exception(
                "Desktop attachment failed"
            )

            return False


# ============================================================
# WALLPAPER PROCESS
# ============================================================

def run_wallpaper_process(html_path):
    """
    Runs in a separate process.

    This process owns the actual wallpaper WebView.
    """

    logger.info("=" * 60)
    logger.info("SceneKraft wallpaper process starting")
    logger.info("PID: %s", os.getpid())
    logger.info("HTML: %s", html_path)
    logger.info("=" * 60)

    html_path = os.path.abspath(html_path)

    if not os.path.isfile(html_path):
        logger.error(
            "Wallpaper file does not exist: %s",
            html_path,
        )

        return 1

    try:
        import webview

    except ImportError:
        logger.exception(
            "pywebview is not installed"
        )

        return 1

    file_url = Path(
        html_path
    ).as_uri()

    logger.info(
        "Loading WebView URL: %s",
        file_url,
    )

    try:
        window = webview.create_window(
            title=WALLPAPER_TITLE,
            url=file_url,
            fullscreen=False,
            frameless=True,
            resizable=False,
            background_color="#000000",
            easy_drag=False,
            text_select=False,
            zoomable=False,
            confirm_close=False,
            js_api=None,
        )

    except Exception:
        logger.exception(
            "Failed to create WebView"
        )

        return 1

    def on_shown():
        logger.info(
            "WebView shown event received"
        )

        # IMPORTANT:
        # pywebview window.uid is NOT the Windows HWND.
        hwnd = WindowsAPI.find_window_by_title(
            WALLPAPER_TITLE,
            timeout=10,
        )

        if not hwnd:
            logger.error(
                "Could not find native wallpaper HWND"
            )

            return

        try:
            HWND_FILE.write_text(
                str(hwnd),
                encoding="utf-8",
            )

            logger.info(
                "HWND saved to %s",
                HWND_FILE,
            )

        except Exception:
            logger.exception(
                "Failed to save HWND"
            )

        if WindowsAPI.attach_to_desktop(
            hwnd
        ):
            logger.info(
                "Wallpaper is running on desktop"
            )

        else:
            logger.error(
                "Wallpaper desktop attachment failed"
            )

    try:
        window.events.shown += on_shown

        logger.info(
            "Starting pywebview..."
        )

        webview.start(
            debug=False,
        )

        logger.info(
            "pywebview stopped"
        )

    except Exception:
        logger.exception(
            "pywebview crashed"
        )

        return 1

    finally:
        try:
            if HWND_FILE.exists():
                HWND_FILE.unlink()
        except Exception:
            pass

    return 0


# ============================================================
# WALLPAPER PROCESS MANAGER
# ============================================================

class WallpaperProcessManager:

    def __init__(self):
        self.process = None

    def is_running(self):
        return (
            self.process is not None
            and self.process.poll() is None
        )

    def start(self, html_path):
        if not html_path:
            logger.error(
                "No wallpaper selected"
            )

            return False

        html_path = os.path.abspath(
            html_path
        )

        if not os.path.isfile(html_path):
            logger.error(
                "Wallpaper not found: %s",
                html_path,
            )

            return False

        # Stop an existing wallpaper that this
        # manager currently owns.
        self.stop()

        try:
            if HWND_FILE.exists():
                HWND_FILE.unlink()
        except Exception:
            pass

        if getattr(sys, "frozen", False):
            command = [
                sys.executable,
                "--wallpaper-mode",
                html_path,
            ]

        else:
            command = [
                sys.executable,
                os.path.abspath(__file__),
                "--wallpaper-mode",
                html_path,
            ]

        logger.info(
            "Starting wallpaper subprocess"
        )

        logger.info(
            "Command: %r",
            command,
        )

        try:
            creationflags = 0

            if sys.platform == "win32":
                creationflags = (
                    subprocess.CREATE_NO_WINDOW
                    | subprocess.CREATE_NEW_PROCESS_GROUP
                )

            self.process = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags,
                cwd=os.path.dirname(
                    os.path.abspath(__file__)
                ),
            )

            logger.info(
                "Wallpaper process started. PID=%s",
                self.process.pid,
            )

            return True

        except Exception:
            logger.exception(
                "Failed to start wallpaper process"
            )

            self.process = None

            return False

    def stop(self):
        """
        Explicitly stop the wallpaper.

        This is ONLY called by Disable Wallpaper.
        Closing the manager does not call this method.
        """

        if not self.process:
            return

        process = self.process

        try:
            if process.poll() is None:
                logger.info(
                    "Stopping wallpaper PID=%s",
                    process.pid,
                )

                process.terminate()

                try:
                    process.wait(
                        timeout=WALLPAPER_STOP_TIMEOUT
                    )

                except subprocess.TimeoutExpired:
                    logger.warning(
                        "Wallpaper did not stop; killing"
                    )

                    process.kill()
                    process.wait()

        except Exception:
            logger.exception(
                "Failed to stop wallpaper"
            )

        finally:
            self.process = None

            try:
                if HWND_FILE.exists():
                    HWND_FILE.unlink()
            except Exception:
                pass

    def restart(self, html_path):
        self.stop()
        time.sleep(0.5)
        return self.start(html_path)


# ============================================================
# SCENEKRAFT UI
# ============================================================

class SceneKraftUI:

    def __init__(self, root):
        self.root = root

        self.wallpaper_manager = (
            WallpaperProcessManager()
        )

        self.selected_file = (
            Config.get_wallpaper_path()
        )

        self.starting_from_windows = (
            "--startup" in sys.argv
        )

        self.root.title(
            f"{APP_NAME} {APP_VERSION}"
        )

        self.root.geometry(
            "760x560"
        )

        self.root.resizable(
            False,
            False,
        )

        self.root.configure(
            bg="#080c16"
        )

        self.center_window()

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.on_close,
        )

        self.build_ui()
        self.show_file()

        if self.starting_from_windows:
            self.root.withdraw()

            if (
                self.selected_file
                and os.path.isfile(
                    self.selected_file
                )
            ):
                self.root.after(
                    1500,
                    self.enable_wallpaper,
                )

            else:
                self.root.deiconify()

        self.root.after(
            1000,
            self.monitor_wallpaper,
        )

    def center_window(self):
        self.root.update_idletasks()

        width = 760
        height = 560

        screen_width = (
            self.root.winfo_screenwidth()
        )

        screen_height = (
            self.root.winfo_screenheight()
        )

        x = max(
            0,
            (screen_width - width) // 2,
        )

        y = max(
            0,
            (screen_height - height) // 2,
        )

        self.root.geometry(
            f"{width}x{height}+{x}+{y}"
        )

    def build_ui(self):

        # ----------------------------------------------------
        # Header
        # ----------------------------------------------------

        header = tk.Frame(
            self.root,
            bg="#101827",
            height=125,
        )

        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="SCENEKRAFT",
            font=(
                "Segoe UI",
                10,
                "bold",
            ),
            bg="#101827",
            fg="#3b82f6",
        ).pack(
            pady=(20, 0)
        )

        tk.Label(
            header,
            text="HTML Wallpaper Engine",
            font=(
                "Segoe UI",
                25,
                "bold",
            ),
            bg="#101827",
            fg="white",
        ).pack()

        tk.Label(
            header,
            text=(
                "HTML  •  CSS  •  JavaScript  •  WebView2"
            ),
            font=(
                "Segoe UI",
                9,
            ),
            bg="#101827",
            fg="#64748b",
        ).pack()

        # ----------------------------------------------------
        # Content
        # ----------------------------------------------------

        content = tk.Frame(
            self.root,
            bg="#080c16",
        )

        content.pack(
            fill="both",
            expand=True,
            padx=48,
            pady=28,
        )

        tk.Label(
            content,
            text="WALLPAPER",
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
            bg="#080c16",
            fg="#64748b",
        ).pack(anchor="w")

        # ----------------------------------------------------
        # File card
        # ----------------------------------------------------

        file_card = tk.Frame(
            content,
            bg="#111827",
            height=82,
        )

        file_card.pack(
            fill="x",
            pady=(8, 13),
        )

        file_card.pack_propagate(False)

        self.filename_label = tk.Label(
            file_card,
            text="No wallpaper selected",
            font=(
                "Segoe UI",
                11,
                "bold",
            ),
            bg="#111827",
            fg="#64748b",
            anchor="w",
        )

        self.filename_label.pack(
            padx=18,
            pady=(14, 0),
            anchor="w",
        )

        self.path_label = tk.Label(
            file_card,
            text=(
                "Choose an HTML file from your computer."
            ),
            font=(
                "Segoe UI",
                8,
            ),
            bg="#111827",
            fg="#64748b",
            anchor="w",
        )

        self.path_label.pack(
            padx=18,
            anchor="w",
        )

        # ----------------------------------------------------
        # Browse button
        # ----------------------------------------------------

        self.browse_button = (
            self.make_button(
                content,
                "📁   BROWSE COMPUTER",
                self.browse_wallpaper,
                "#2563eb",
                "#1d4ed8",
            )
        )

        self.browse_button.pack(
            anchor="w"
        )

        # ----------------------------------------------------
        # Control card
        # ----------------------------------------------------

        control_card = tk.Frame(
            content,
            bg="#101827",
        )

        control_card.pack(
            fill="x",
            pady=24,
        )

        tk.Label(
            control_card,
            text="WALLPAPER CONTROL",
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
            bg="#101827",
            fg="#64748b",
        ).pack(
            anchor="w",
            padx=20,
            pady=(14, 9),
        )

        controls = tk.Frame(
            control_card,
            bg="#101827",
        )

        controls.pack(
            pady=(0, 16)
        )

        self.enable_button = (
            self.make_button(
                controls,
                "✓   ENABLE WALLPAPER",
                self.enable_wallpaper,
                "#16a34a",
                "#15803d",
            )
        )

        self.enable_button.pack(
            side="left",
            padx=5,
        )

        self.disable_button = (
            self.make_button(
                controls,
                "×   DISABLE WALLPAPER",
                self.disable_wallpaper,
                "#263044",
                "#334155",
            )
        )

        self.disable_button.pack(
            side="left",
            padx=5,
        )

        # ----------------------------------------------------
        # Startup card
        # ----------------------------------------------------

        startup_card = tk.Frame(
            content,
            bg="#111827",
        )

        startup_card.pack(
            fill="x"
        )

        startup_enabled = (
            Startup.is_enabled()
        )

        self.startup_var = (
            tk.BooleanVar(
                value=startup_enabled
            )
        )

        tk.Checkbutton(
            startup_card,
            text="Start SceneKraft with Windows",
            variable=self.startup_var,
            command=self.on_startup_changed,
            font=(
                "Segoe UI",
                10,
            ),
            bg="#111827",
            fg="white",
            activebackground="#111827",
            activeforeground="white",
            selectcolor="#111827",
            cursor="hand2",
        ).pack(
            side="left",
            padx=16,
            pady=13,
        )

        self.startup_status = tk.Label(
            startup_card,
            text=(
                "Enabled"
                if startup_enabled
                else "Disabled"
            ),
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
            bg="#111827",
            fg=(
                "#4ade80"
                if startup_enabled
                else "#64748b"
            ),
        )

        self.startup_status.pack(
            side="right",
            padx=16,
        )

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        self.status_label = tk.Label(
            content,
            text="● Wallpaper disabled",
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
            bg="#080c16",
            fg="#f87171",
        )

        self.status_label.pack(
            pady=13
        )

        # ----------------------------------------------------
        # Footer
        # ----------------------------------------------------

        tk.Label(
            self.root,
            text=(
                "SceneKraft  •  User mode  •  "
                "No administrator permission required"
            ),
            font=(
                "Segoe UI",
                8,
            ),
            bg="#080c16",
            fg="#334155",
        ).pack(
            pady=(0, 14)
        )

    @staticmethod
    def make_button(
        parent,
        text,
        command,
        bg,
        active,
    ):
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=(
                "Segoe UI",
                10,
                "bold",
            ),
            bg=bg,
            fg="white",
            activebackground=active,
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=23,
            pady=11,
        )

    def set_status(self, text, color):
        try:
            self.status_label.config(
                text=text,
                fg=color,
            )

        except tk.TclError:
            pass

    def show_file(self):
        if self.selected_file:

            self.filename_label.config(
                text=os.path.basename(
                    self.selected_file
                ),
                fg="#ffffff",
            )

            self.path_label.config(
                text=self.selected_file,
                fg="#64748b",
            )

            self.browse_button.config(
                text="📁   CHANGE WALLPAPER"
            )

        else:

            self.filename_label.config(
                text="No wallpaper selected",
                fg="#64748b",
            )

            self.path_label.config(
                text=(
                    "Choose an HTML file from your computer."
                ),
                fg="#64748b",
            )

            self.browse_button.config(
                text="📁   BROWSE COMPUTER"
            )

    def browse_wallpaper(self):
        path = filedialog.askopenfilename(
            title="Select HTML Wallpaper",
            initialdir=os.path.expanduser("~"),
            filetypes=[
                (
                    "HTML files",
                    "*.html *.htm",
                ),
                (
                    "All files",
                    "*.*",
                ),
            ],
        )

        if not path:
            return

        self.selected_file = os.path.abspath(
            path
        )

        Config.set_wallpaper_path(
            self.selected_file
        )

        self.show_file()

        self.set_status(
            "● Wallpaper selected",
            "#60a5fa",
        )

    def enable_wallpaper(self):

        if self.wallpaper_manager.is_running():

            self.set_status(
                "● Wallpaper enabled",
                "#4ade80",
            )

            return

        if not self.selected_file:

            messagebox.showwarning(
                APP_NAME,
                "Select an HTML wallpaper first.",
            )

            return

        if not os.path.isfile(
            self.selected_file
        ):

            messagebox.showerror(
                APP_NAME,
                "The selected HTML file no longer exists.",
            )

            return

        self.set_status(
            "● Loading wallpaper...",
            "#facc15",
        )

        if not self.wallpaper_manager.start(
            self.selected_file
        ):

            messagebox.showerror(
                APP_NAME,
                "Failed to start the wallpaper process.\n\n"
                f"Check:\n{LOG_FILE}",
            )

            self.set_status(
                "● Error starting wallpaper",
                "#f87171",
            )

            return

        self.root.after(
            2000,
            self.check_wallpaper_status,
        )

    def disable_wallpaper(self):
        """
        Explicitly stop wallpaper.
        """

        self.wallpaper_manager.stop()

        self.set_status(
            "● Wallpaper disabled",
            "#f87171",
        )

        self.enable_button.config(
            bg="#263044"
        )

    def check_wallpaper_status(self):

        if self.wallpaper_manager.is_running():

            self.set_status(
                "● Wallpaper enabled",
                "#4ade80",
            )

            self.enable_button.config(
                bg="#16a34a"
            )

        else:

            self.set_status(
                "● Wallpaper failed to start",
                "#f87171",
            )

            self.enable_button.config(
                bg="#263044"
            )

    def monitor_wallpaper(self):
        try:

            if self.wallpaper_manager.is_running():

                self.set_status(
                    "● Wallpaper enabled",
                    "#4ade80",
                )

            else:

                if (
                    self.enable_button.cget("bg")
                    == "#16a34a"
                ):

                    self.set_status(
                        "● Wallpaper stopped",
                        "#f87171",
                    )

                    self.enable_button.config(
                        bg="#263044"
                    )

            self.root.after(
                1000,
                self.monitor_wallpaper,
            )

        except tk.TclError:
            pass

    def on_startup_changed(self):
        enabled = self.startup_var.get()

        if Startup.set_enabled(enabled):

            self.startup_status.config(
                text=(
                    "Enabled"
                    if enabled
                    else "Disabled"
                ),
                fg=(
                    "#4ade80"
                    if enabled
                    else "#64748b"
                ),
            )

        else:

            self.startup_var.set(
                not enabled
            )

            messagebox.showerror(
                APP_NAME,
                "Failed to modify Windows startup settings.",
            )

    def on_close(self):
        """
        Close ONLY the manager window.

        IMPORTANT:
        The wallpaper subprocess is intentionally NOT stopped.
        """

        logger.info(
            "Closing SceneKraft manager UI"
        )

        # DO NOT call:
        # self.wallpaper_manager.stop()

        try:
            self.root.destroy()

        except tk.TclError:
            pass


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "SceneKraft HTML Wallpaper Engine"
        )
    )

    parser.add_argument(
        "--wallpaper-mode",
        metavar="HTML",
        help=(
            "Internal wallpaper process mode"
        ),
    )

    parser.add_argument(
        "--startup",
        action="store_true",
        help=(
            "Started by Windows startup"
        ),
    )

    args = parser.parse_args()

    # --------------------------------------------------------
    # Wallpaper subprocess
    # --------------------------------------------------------

    if args.wallpaper_mode is not None:

        if not args.wallpaper_mode:

            logger.error(
                "No HTML path specified"
            )

            return 1

        return run_wallpaper_process(
            args.wallpaper_mode
        )

    # --------------------------------------------------------
    # Manager UI
    # --------------------------------------------------------

    try:
        root = tk.Tk()

    except Exception:
        logger.exception(
            "Failed to initialize Tkinter"
        )

        return 1

    try:

        SceneKraftUI(root)

        root.mainloop()

    except Exception:
        logger.exception(
            "SceneKraft UI crashed"
        )

        return 1

    return 0


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    if sys.platform != "win32":

        print(
            "SceneKraft requires Windows.",
            file=sys.stderr,
        )

        sys.exit(1)

    sys.exit(
        main()
    )
