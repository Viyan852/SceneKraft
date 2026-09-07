SceneKraft

A lightweight HTML wallpaper engine for Windows.

SceneKraft lets you use your own HTML, CSS and JavaScript projects as desktop wallpapers.

Features
HTML wallpapers
CSS and JavaScript
Browse wallpapers from anywhere
Enable / Disable wallpaper
Remembers your wallpaper
Start with Windows
WebView2 rendering
Lightweight Python application
Windows Requirements
Windows 10 or Windows 11
64-bit recommended
Microsoft Edge WebView2 Runtime
Run from source

Install dependencies:

python -m pip install -r requirements.txt


Run:

python app.py

Build Windows
python -m PyInstaller --onefile --windowed --name SceneKraft app.py


The executable will be:

dist/SceneKraft.exe

HTML Wallpaper Example
my-wallpaper/
├── index.html
├── style.css
├── script.js
└── images/
    └── background.jpg


Relative CSS, JavaScript and image files can be used normally.

License

SceneKraft is released under the MIT License.

See LICENSE.