#!/usr/bin/env python3

import argparse
import os


# --- Arguments ---
argument_parser = argparse.ArgumentParser(description="Find all empty sub folders of a folder. Ignore folders from .gitignore file if it exists.")

# Project folder argument
argument_parser.add_argument('path', help='Path of the folder containing your `.xcodeproj` folder.')


# --- Parse arguments ---
args = argument_parser.parse_args()


# Folders to ignore
ignored_folders = {
    'DerivedData',
    '.git',
}

# Remove ending slashes to path
path = args.path
while path and path[-1] == os.path.sep:
    path = path[:-1]

# Walk to find empty folders
for (dirpath, dirnames, filenames) in os.walk(path):
    relative_dirpath = dirpath[len(path):]

    # Filter folders to ignore
    folder_parts = set(relative_dirpath.split(os.path.sep))
    if ignored_folders & folder_parts:
        continue
        
    if not dirnames and not filenames:
        print(relative_dirpath)
