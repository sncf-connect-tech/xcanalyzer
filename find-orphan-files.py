#!/usr/bin/env python3

import argparse
import os

from xcanalyzer.argparse import parse_ignored_folders
from xcanalyzer.xcodeproject.parsers import XcProjectParser
from xcanalyzer.xcodeproject.generators import XcProjReporter
from xcanalyzer.xcodeproject.exceptions import XcodeProjectReadException


# --- Arguments ---
argument_parser = argparse.ArgumentParser(description="List files from the folder not referenced in the Xcode project. Ignore folders named `.git` and `DerivedData`.")

# Project folder argument
argument_parser.add_argument('path',
                             help='Path of the folder containing your `.xcodeproj` folder.')

# Ignore folders argument
argument_parser.add_argument('-d', '--ignore-dir',
                             action='append',
                             dest='ignored_folders',
                             metavar='<dirpath>',
                             help='Path or name of a folder to ignore.')

# Mode
argument_parser.add_argument('-m', '--mode',
                             choices=['all', 'project', 'target', 'referenced'],
                             dest='orphan_mode',
                             default='all',
                             help="Orphan mode:\
                                   'referenced' means all '*Info.plist' and '*.h' files referenced by at least one target.\
                                   'project' means all files in the folder but not referenced in the project.\
                                   'target' means all files in the project but not referenced by any target.\
                                   'all' (default) means all files in the folder but not referenced by any target (neither the project).")


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

# Xcode code project reader
xcode_project_reader = XcProjectParser(path)

# Loading the project
try:
    xcode_project_reader.load()
except XcodeProjectReadException as e:
    print("An error occurred when loading Xcode project: {}".format(e.message))
    exit()

# Reporter
reporter = XcProjReporter(xcode_project_reader.object)
reporter.print_orphan_files(ignored_dirpaths,
                            ignored_dirs,
                            mode=args.orphan_mode)
