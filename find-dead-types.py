#!/usr/bin/env python3

from termcolor import cprint

import argparse
import os

from xcanalyzer.xcodeproject.parsers import XcProjectParser
from xcanalyzer.xcodeproject.generators import OccurrencesReporter
from xcanalyzer.xcodeproject.exceptions import XcodeProjectReadException
from xcanalyzer.language.models import SwiftTypeType, ObjcTypeType


# --- Arguments ---
argument_parser = argparse.ArgumentParser(description="List all types that are unused in the project.")

# Project folder argument
argument_parser.add_argument('path',
                             help='Path of the folder containing your `.xcodeproj` folder.')

# App name
argument_parser.add_argument('app',
                             help='Name of the iOS app target.')


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
swift_types = app_target.swift_types_dependencies_filtered(type_not_in={SwiftTypeType.EXTENSION})
objc_types = app_target.objc_types_dependencies_filtered(type_not_in={ObjcTypeType.CATEGORY, ObjcTypeType.CONSTANT})  # temporary exclude constants from objc types
type_occurrences_set = xcode_project_reader.find_type_occurrences_from_files(
    swift_types + objc_types,
    from_target=app_target)

# Print occurrences for each type
occurrences_reporter = OccurrencesReporter()
occurrences_reporter.print_type_occurrences_multiple_types(type_occurrences_set)

# TODO:
# save/load cache for type occurrences
# report print really dead types: manage a mode:
    # display all
    # display only types with 0 outside occurrence
    # display only types with exactly 1 inside occurrence (the declaration)
    # ...
