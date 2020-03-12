#!/usr/bin/env python3

import argparse
import os

from xcanalyzer.xcodeproject.parsers import XcProjectParser
from xcanalyzer.xcodeproject.generators import XcProjReporter
from xcanalyzer.xcodeproject.exceptions import XcodeProjectReadException


# --- Arguments ---
argument_parser = argparse.ArgumentParser(description="Gives all the Swift or Obj-C types of the project that use a given type.")

# Project folder argument
argument_parser.add_argument('path',
                             help='Path of the folder containing your `.xcodeproj` folder.')

# App name
argument_parser.add_argument('app',
                             help='Name of the iOS app target.')

# Type name
argument_parser.add_argument('type',
                             help='Name of the Swift or Objective-C type to search from.')


# --- Parse arguments ---
args = argument_parser.parse_args()

# Argument: path => Remove ending slashes from path
path = args.path
while path and path[-1] == os.path.sep:
    path = path[:-1]


# Xcode code project reader
xcode_project_reader = XcProjectParser(path)

# Loading the project
try:
    xcode_project_reader.load()

    # Parse Swift files
    xcode_project_reader.parse_swift_files()

    # Parse Objective-C files (always because Swift extension can be of objc types)
    xcode_project_reader.parse_objc_files()
except XcodeProjectReadException as e:
    print("An error occurred when loading Xcode project: {}".format(e.message))
    exit()


# App target
app_target = xcode_project_reader.xc_project.target_with_name(args.app)
if not app_target:
    raise ValueError("No app target found with name '{}'.".format(args.app))

# Find occurrences
occurrences_from_types = xcode_project_reader.find_type_occurrences_from_types(args.type, from_target=app_target)

# Reporter
print()
print("--- Occurrences results ---")
reporter = XcProjReporter(xcode_project_reader.xc_project)
reporter.print_types_occurrences_from_types(occurrences_from_types)
