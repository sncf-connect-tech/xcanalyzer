#!/usr/bin/env python3

import argparse

from xcanalyzer.xcodeproject.parsers import XcodeProjectReader
from xcanalyzer.xcodeproject.exceptions import XcodeProjectReadException
from xcanalyzer.xcodeproject.generators import XcodeProjectGraphGenerator
from xcanalyzer.xcodeproject.models import XcTarget


# Arguments
argument_parser = argparse.ArgumentParser(description="Generate targets dependencies graphs of a Xcode project.")

# Project folder argument
argument_parser.add_argument('path', help='Path of the folder containing your `.xcodeproj` folder.')

# Parse args
args = argument_parser.parse_args()

# Project folder
xcode_project_path = args.path


# Xcode code project reader
xcode_project_reader = XcodeProjectReader(xcode_project_path)

# Loading the project
try:
    xcode_project_reader.load()
except XcodeProjectReadException as e:
    print("An error occurred when loading Xcode projet: {}".format(e.message))
    exit()

graph_generator = XcodeProjectGraphGenerator(xcode_project_reader)

graph_generator.generate_targets_dependencies_graph(open_pdf=True,
                                                    filepath='build/all_targets_dependencies_graph',
                                                    title='All Targets Dependencies Graph')

graph_generator.generate_targets_dependencies_graph(open_pdf=True,
                                                    filepath='build/framework_targets_dependencies_graph',
                                                    title='Framework Targets Dependencies Graph',
                                                    including_types=set([XcTarget.Type.FRAMEWORK]))
