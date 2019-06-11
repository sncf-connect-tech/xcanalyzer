#!/usr/bin/env python3

import argparse

from xcanalyzer.xcodeproject.parsers import XcProjectParser
from xcanalyzer.xcodeproject.exceptions import XcodeProjectReadException
from xcanalyzer.xcodeproject.generators import XcProjectGraphGenerator
from xcanalyzer.xcodeproject.models import XcTarget


# --- Arguments ---
argument_parser = argparse.ArgumentParser(description="Generate targets dependencies graphs of a Xcode project.")

# Project folder argument
argument_parser.add_argument('path', help='Path of the folder containing your `.xcodeproj` folder.')

# Dependency type
argument_parser.add_argument('-t', '--dependency-type',
                             choices=['build', 'linked', 'embed'],
                             dest='dependency_type',
                             required=True,
                             help="Type of dependency to look for. \
                                   Available types are target 'build' dependencies, \
                                   'linked' framework dependencies \
                                   and 'embed' framework dependencies.")

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
                             metavar='<title>',
                             help='Title for the generated graph.')

# Output file argument
argument_parser.add_argument('-o', '--output-file',
                             dest='output_filepath',
                             metavar='<filepath>',
                             help='Filepath of the generated PDF file.')

# Output format argument
argument_parser.add_argument('-f', '--output-format',
                             choices=['pdf', 'png'],
                             default='pdf',
                             dest='output_format',
                             help='Output format of the generated file (PDF and PNG are supported).')


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
graph_generator = XcProjectGraphGenerator(xcode_project_reader.object)

# Default file path and title
if args.dependency_type == 'build':
    filepath = output_filepath or 'build/build_dependencies_graph'
    title = args.title or 'Targets Build-Dependencies Graph'
elif args.dependency_type == 'linked':
    filepath = output_filepath or 'build/linked_dependencies_graph'
    title = args.title or 'Targets Linked-Framework-Dependencies Graph'
elif args.dependency_type == 'embed':
    filepath = output_filepath or 'build/embed_dependencies_graph'
    title = args.title or 'Targets Embed-Framework-Dependencies Graph'
else:
    raise Exception("dependency_type '{}' not supported".format(args.dependency_type))

if args.framework_only:
    filepath += '__only_frameworks'
    title += ' (only frameworks)'

# Including types of frameworks
including_types = set([XcTarget.Type.FRAMEWORK]) if args.framework_only else set()


# --- Generate graph ---
graph_generated = graph_generator.generate_targets_dependencies_graph(output_format=args.output_format,
                                                                      dependency_type=args.dependency_type,
                                                                      preview=args.open_preview_graph,
                                                                      display_graph_source=args.display_graph_source,
                                                                      filepath=filepath,
                                                                      title=title,
                                                                      including_types=including_types)

if graph_generated:
    if not args.display_graph_source:
        print("Generated: {}.{}".format(filepath, args.output_format))
else:
    print("An error occurred generating graph: {}".format(filepath))
    exit()