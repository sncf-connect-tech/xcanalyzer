#!/usr/bin/env python3

import argparse

from xcanalyzer.xcodeproject.parsers import XcProjectParser
from xcanalyzer.xcodeproject.exceptions import XcodeProjectReadException
from xcanalyzer.xcodeproject.generators import XcodeProjectGraphGenerator
from xcanalyzer.xcodeproject.models import XcTarget


# --- Arguments ---
argument_parser = argparse.ArgumentParser(description="Generate targets dependencies graphs of a Xcode project.")

# Project folder argument
argument_parser.add_argument('path', help='Path of the folder containing your `.xcodeproj` folder.')

# Open graph argument
argument_parser.add_argument('-p', '--preview',
                             dest='open_preview_graph',
                             action='store_true', 
                             help='Open the generated graph in Preview.')

# Display graph source
argument_parser.add_argument('--graph-source',
                             dest='display_graph_source',
                             action='store_true', 
                             help='Display graphviz graph source in standard output.')

# Framework only argument
argument_parser.add_argument('--framework-only',
                             dest='framework_only',
                             action='store_true', 
                             help='Ignore all non touch framework targets.')

# Title only argument
argument_parser.add_argument('--title',
                             dest='title',
                             help='Title for the generated graph.')

# Output file argument
argument_parser.add_argument('-o', '--output-file',
                             dest='output_filepath',
                             help='Filepath of the generated PDF file.')

# Output format argument
argument_parser.add_argument('-f', '--output-format',
                             choices=['pdf', 'png'],
                             default='pdf',
                             dest='output_format',
                             help='Output format of the granerated file (PDF and PNG are supported).')


# --- Parse arguments ---
args = argument_parser.parse_args()

# Project folder
xcode_project_path = args.path

# Xcode code project reader
xcode_project_reader = XcProjectParser(xcode_project_path)

# Output filepath
if args.output_filepath:
    if args.output_filepath[:-4] in {'pdf', 'png'}:
        output_filepath = args.output_filepath[:-4]
    else:
        output_filepath = args.output_filepath
else:
    output_filepath = None

# Loading the project
try:
    xcode_project_reader.load()
except XcodeProjectReadException as e:
    print("An error occurred when loading Xcode project: {}".format(e.message))
    exit()

# Generator
graph_generator = XcodeProjectGraphGenerator(xcode_project_reader)

# Generate graph
if args.framework_only:
    filepath = output_filepath or 'build/framework_targets_dependencies_graph'
    title = args.title or 'Framework Targets Dependencies Graph'
    graph_generated = graph_generator.generate_targets_dependencies_graph(output_format=args.output_format,
                                                                          preview=args.open_preview_graph,
                                                                          display_graph_source=args.display_graph_source,
                                                                          filepath=filepath,
                                                                          title=title,
                                                                          including_types=set([XcTarget.Type.FRAMEWORK]))
else:
    filepath = output_filepath or 'build/all_targets_dependencies_graph'
    title = args.title or 'All Targets Dependencies Graph'
    graph_generated = graph_generator.generate_targets_dependencies_graph(output_format=args.output_format,
                                                                          preview=args.open_preview_graph,
                                                                          display_graph_source=args.display_graph_source,
                                                                          filepath=filepath,
                                                                          title=title)

if graph_generated:
    if not args.display_graph_source:
        print("Generated: {}.{}".format(filepath, args.output_format))
else:
    print("An error occurred generating graph: {}".format(filepath))
    exit()