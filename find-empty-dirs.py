#!/usr/bin/env python3

import argparse
import os

from xcanalyzer.xcodeproject.generators import FolderReporter



# --- Arguments ---
argument_parser = argparse.ArgumentParser(description="Find all empty sub folders of a folder. Ignore folders named `.git` or `DerivedData`.")

# Project folder argument
argument_parser.add_argument('path', help='Path of the folder containing your `.xcodeproj` folder.')

# Ignore folders argument
argument_parser.add_argument('-i', '--ignore-dir',
                             action='append',
                             dest='ignored_folders',
                             metavar='<dirpath>',
                             help='Path of a folder to ignore.')


# --- Parse arguments ---
args = argument_parser.parse_args()

# Argument: path => Remove ending slashes from path
path = args.path
while path and path[-1] == os.path.sep:
    path = path[:-1]

# Folder to ignore given as argument
arged_ignored_folders = set(args.ignored_folders or [])
ignored_folders = set()
for folder in arged_ignored_folders:
    # Remove ending slashes from given ignored folder paths
    while folder and folder[-1] == os.path.sep:
        folder = folder[:-1]
    ignored_folders.add(folder)

# Forced folders to ignore
ignored_folders = {
    'DerivedData',
    '.git',
} | ignored_folders

# Ignored path and folders
ignored_dirpaths = {f for f in ignored_folders if os.path.sep in f}
ignored_dirs = ignored_folders - ignored_dirpaths
ignored_dirpaths = set(map(lambda f: f if f.startswith(os.path.sep) else '/{}'.format(f), ignored_dirpaths))


# Report
reporter = FolderReporter(path, ignored_dirpaths, ignored_dirs)
reporter.print_empty_dirs()
