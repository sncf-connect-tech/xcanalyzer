#!/usr/bin/env python3

import argparse

from xcanalyzer.xcodeproject.parsers import XcProjectParser
from xcanalyzer.xcodeproject.generators import XcProjReporter


# --- Arguments ---
argument_parser = argparse.ArgumentParser(description="List all targets and files of the Xcode project.")

# Project folder argument
argument_parser.add_argument('path',
                             help='Path of the folder containing your `.xcodeproj` folder.')


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
reporter = XcProjReporter(xcode_project_reader.xcode_project)
reporter.print_targets()