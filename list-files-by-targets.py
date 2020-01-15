#!/usr/bin/env python3

import argparse

from xcanalyzer.xcodeproject.parsers import XcProjectParser
from xcanalyzer.xcodeproject.generators import XcProjReporter
from xcanalyzer.xcodeproject.exceptions import XcodeProjectReadException


# --- Arguments ---
argument_parser = argparse.ArgumentParser(description="List all targets and files of the Xcode project.")

# Project folder argument
argument_parser.add_argument('path',
                             help='Path of the folder containing your `.xcodeproj` folder.')

# Only "shared" files between targets
argument_parser.add_argument('-s', '--only-shared',
                             dest='only_shared',
                             action='store_true', 
                             help='Give the list of files used by multiple targets.')


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
reporter = XcProjReporter(xcode_project_reader.xc_project)
if args.only_shared:
    reporter.print_shared_files()
else:
    reporter.print_files_by_targets()
    reporter.print_files_summary()