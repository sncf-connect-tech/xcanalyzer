#!/usr/bin/env python3

import argparse

from xcanalyzer.xcodeproject.parsers import XcProjectParser
from xcanalyzer.xcodeproject.exceptions import XcodeProjectReadException
from xcanalyzer.xcodeproject.generators import XcProjReporter


# --- Arguments ---
argument_parser = argparse.ArgumentParser(description="List all targets and files of the Xcode project.")

# Project folder argument
argument_parser.add_argument('path',
                             help='Path of the folder containing your `.xcodeproj` folder.')

# Sorted by name argument
argument_parser.add_argument('-n', '--name-sorted',
                             dest='sorted_by_name',
                             action='store_true', 
                             help='Give the list of targets sorted by name. So they are not grouped by type.')

# Verbose argument
argument_parser.add_argument('-v', '--verbose',
                             dest='verbose',
                             action='store_true', 
                             help=".")


# --- Parse arguments ---
args = argument_parser.parse_args()

# Xcode code project reader
xcode_project_reader = XcProjectParser(args.path)

# Loading the project
try:
    xcode_project_reader.load()
except XcodeProjectReadException as e:
    print("An error occurred when loading Xcode project: {}".format(e.message))
    exit()

# Reporter
reporter = XcProjReporter(xcode_project_reader.object)
reporter.print_targets(by_type=(not args.sorted_by_name), verbose=args.verbose)
if not args.sorted_by_name:
    reporter.print_targets_summary()