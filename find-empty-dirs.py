#!/usr/bin/env python3

import argparse
import os

from xcanalyzer.argparse import parse_ignored_folders
from xcanalyzer.xcodeproject.generators import FolderReporter



# --- Arguments ---
argument_parser = argparse.ArgumentParser(description="Find all empty sub folders of a folder. Ignore folders named `.git` and `DerivedData`.")

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

# Parse ignored folders
ignored_folders = set(args.ignored_folders or []) | {
    'DerivedData',
    '.git',
}
ignored_dirpaths, ignored_dirs = parse_ignored_folders(ignored_folders)


# Report
reporter = FolderReporter(path, ignored_dirpaths, ignored_dirs)
reporter.print_empty_dirs()
