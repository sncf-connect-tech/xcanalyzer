#!/usr/bin/env python3

import argparse

from xcanalyzer.xcodeproject.parsers import XcodeProjectReader
from xcanalyzer.xcodeproject.exceptions import XcodeProjectReadException
from xcanalyzer.xcodeproject.generators import XcodeProjectGraphGenerator
from xcanalyzer.xcodeproject.models import XcTarget


# --- Arguments ---
argument_parser = argparse.ArgumentParser(description="Generate targets dependencies graphs of a Xcode project.")

# Project folder argument
argument_parser.add_argument('path', help='Path of the folder containing your `.xcodeproj` folder.')

# Open PDF argument
argument_parser.add_argument('-p', '--preview',
                             dest='open_preview_graph',
                             action='store_const', 
                             default=False,
                             const=True,
                             help='Open the generated graph in Preview.')

# Framework only argument
argument_parser.add_argument('-f', '--framework-only',
                             dest='framework_only',
                             action='store_const', 
                             default=False,
                             const=True,
                             help='Ignore all non touch framework targets.')

# --- Parse arguments ---
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

# Generator
graph_generator = XcodeProjectGraphGenerator(xcode_project_reader)

if args.framework_only:
    filepath = 'build/framework_targets_dependencies_graph'
    graph_generated = graph_generator.generate_targets_dependencies_graph(open_pdf=args.open_preview_graph,
                                                                          filepath=filepath,
                                                                          title='Framework Targets Dependencies Graph',
                                                                          including_types=set([XcTarget.Type.FRAMEWORK]))
else:
    filepath='build/all_targets_dependencies_graph'
    graph_generated = graph_generator.generate_targets_dependencies_graph(open_pdf=args.open_preview_graph,
                                                                          filepath=filepath,
                                                                          title='All Targets Dependencies Graph')

if graph_generated:
    print("Graph generated file: {}.pdf".format(filepath))
