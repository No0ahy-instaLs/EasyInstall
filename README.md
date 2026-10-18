
# EasyInstall

A Windows desktop software hub built with Python and Tkinter.

## Requirements

- Windows 10 or Windows 11
- Python 3.10 or newer to build
- Windows Package Manager (winget)
- Internet access for downloads

## Run from source

Open a terminal in the EasyInstall folder and run:

    python main.py

## Build the executable

Run:

    build.bat

The executable will be created at:

    dist/EasyInstall.exe

## Adding applications

Edit the APPS list in main.py.

Each entry requires:
- name: Display name
- id: Exact winget package ID
- category: Library category
- description: Short description

Check package IDs against the official winget package repository before adding them.
