#!/usr/bin/env python3

from termcolor import cprint

import argparse
import os

from xcanalyzer.xcodeproject.parsers import XcProjectParser
from xcanalyzer.xcodeproject.generators import XcProjReporter
from xcanalyzer.xcodeproject.exceptions import XcodeProjectReadException


# --- Arguments ---
argument_parser = argparse.ArgumentParser(description="List all occurrences of a Swift or Objective-C type in the code of the whole Xcode project.")

# Project folder argument
argument_parser.add_argument('path',
                             help='Path of the folder containing your `.xcodeproj` folder.')

# App name
argument_parser.add_argument('type',
                             help='Name of the Swift or Objective-C type to search for.')


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

    # Find occurrences of the given type
    report = xcode_project_reader.find_occurrences_of(args.type)
except XcodeProjectReadException as e:
    print("An error occurred when loading Xcode project: {}".format(e.message))
    exit()

# Place of the type declaration
cprint("Declaration of type `{}` was found in file `{}`".format(
    report['swift_or_objc_type'].name,
    report['source_file_containing_type_definition'].filepath),
    attrs=['bold'])

# Other occurrences in the declaration source file
occurrences_count = report['occurrences_count_in_definition_file']
if occurrences_count >= 2:
    cprint("In this file, {} line(s) of code contain(s) occurrence(s) of this type (excluding the line containing the declaration).".format(occurrences_count - 1))

# Other files that contains occurrences of the type
cprint("Other sources files containing occurrences of `{}`:".format(report['swift_or_objc_type'].name), attrs=['bold'])
source_files = report["source_files_in_which_type_occurs"]
for source_file in source_files:
    print(source_file.filepath)