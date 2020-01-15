#!/usr/bin/env python3

import argparse
import os

from xcanalyzer.xcodeproject.parsers import XcProjectParser
from xcanalyzer.xcodeproject.generators import XcProjReporter
from xcanalyzer.xcodeproject.exceptions import XcodeProjectReadException


# --- Arguments ---
argument_parser = argparse.ArgumentParser(description="List all types (protocols, extensions, structs, enums and classes) by file and by target.")

# Project folder argument
argument_parser.add_argument('path',
                             help='Path of the folder containing your `.xcodeproj` folder.')

# Filter languages
argument_parser.add_argument('-l', '--languages',
                             choices=['all', 'swift', 'objc'],
                             default='all',
                             dest='language',
                             help='Language for which the types are given: Objective-C, Swift or both.')

# Display files
argument_parser.add_argument('-f', '--display-files',
                             dest='display_files',
                             action='store_true', 
                             help='Display file paths in which the types are defined.')


# --- Parse arguments ---
args = argument_parser.parse_args()

# Argument: path => Remove ending slashes from path
path = args.path
while path and path[-1] == os.path.sep:
    path = path[:-1]

if args.language == 'all':
    languages = {'swift', 'objc'}
else:
    languages = {args.language}

# Xcode code project reader
xcode_project_reader = XcProjectParser(path)

# Loading the project
try:
    xcode_project_reader.load()

    # Parse Swift files
    if 'swift' in languages:
        xcode_project_reader.parse_swift_files()

    # Parse Objective-C files (always because Swift extension can be of objc types)
    xcode_project_reader.parse_objc_files()
except XcodeProjectReadException as e:
    print("An error occurred when loading Xcode project: {}".format(e.message))
    exit()

# Reporter
reporter = XcProjReporter(xcode_project_reader.xc_project)
reporter.print_types_by_file(languages=languages, display_files=args.display_files)
reporter.print_types_summary(languages=languages)