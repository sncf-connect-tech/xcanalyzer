#!/usr/bin/env python3

import argparse

from xcanalyzer.xcodeproject.parsers import XcProjectParser
from xcanalyzer.xcodeproject.generators import XcProjReporter
from xcanalyzer.xcodeproject.exceptions import XcodeProjectReadException


# --- Arguments ---
argument_parser = argparse.ArgumentParser(description="Find all xcodeproj groups with potential unconformance.")

# Project folder argument
argument_parser.add_argument('path',
                             help='Path of the folder containing your `.xcodeproj` folder.')

# Sorted by name argument
argument_parser.add_argument('--empty',
                             dest='empty_groups',
                             action='store_true', 
                             help='Give the list of empty groups in the Xcode project.')


# --- Parse arguments ---
args = argument_parser.parse_args()

# Xcode code project reader
xcode_project_reader = XcProjectParser(args.path, verbose=False)

# Loading the project
try:
    xcode_project_reader.load()
except XcodeProjectReadException as e:
    print("An error occurred when loading Xcode project: {}".format(e.message))
    exit()

# Reporter
reporter = XcProjReporter(xcode_project_reader.object)
reporter.print_groups(filter_empty=args.empty_groups)
