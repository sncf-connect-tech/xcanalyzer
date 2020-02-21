#!/usr/bin/env python3

from termcolor import cprint

import argparse
import os

from xcanalyzer.xcodeproject.parsers import XcProjectParser
from xcanalyzer.xcodeproject.generators import OccurrencesReporter
from xcanalyzer.xcodeproject.exceptions import XcodeProjectReadException


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

# App target dependencies sorted by name
app_target_dependencies = list(app_target.dependencies_all)
app_target_dependencies.sort(key=lambda t: t.name.lower())
targets = app_target_dependencies + [app_target]

objc_classes = set()
for target in targets:
    objc_classes |= set(target.objc_classes)

objc_classes = list(objc_classes)
objc_classes.sort(key=lambda t: t.name.lower())
total_class_count = len(objc_classes)

occurrences_reporter = OccurrencesReporter()
for index, objc_class in enumerate(objc_classes):
    report = xcode_project_reader.find_occurrences_of(objc_class.name)
    
    # occurrences_reporter.print_type_occurrences_report(report, indent=4)

    inside_count = report['occurrences_count_in_definition_file']
    outside_count = len(report['source_files_in_which_type_occurs'])

    print("{:<7} {:<15} {:<40} \"Inside decl. occurrences\": {:<3} | \"Outside decl. occurrences\": {:<3}".format(
        '/'.join([str(index), str(total_class_count)]),
        objc_class.type_identifier,
        objc_class.name,
        inside_count,
        outside_count))