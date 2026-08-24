@echo off
cd /d "%~dp0\.."
python -m pip install -q pyinstaller Pillow psutil
pyinstaller --noconfirm --clean --windowed --name ASFDesktop --add-data "ui/icons/png;ui/icons/png" --hidden-import PIL --hidden-import psutil main.py
echo Artefato: dist\ASFDesktop\
