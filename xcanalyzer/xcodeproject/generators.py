from graphviz import Digraph
from termcolor import cprint

from .models import XcTarget


class XcProjectGraphGenerator():

    def __init__(self, xcode_project):
        self.xcode_project = xcode_project
    
    def generate_targets_dependencies_graph(self,
                                            output_format='pdf',
                                            preview=False,
                                            display_graph_source=False,
                                            filepath=None,
                                            title=None,
                                            including_types=set()):
        if not filepath or not title:
            return False
        
        if output_format not in {'pdf', 'png'}:
            return False

        graph = Digraph(filename=filepath,
                        format=output_format,
                        engine='dot',
                        graph_attr={
                            'fontname': 'Courier',
                            'pack': 'true',
                        },
                        node_attr={
                            'shape': 'box',
                            'fontname': 'Courier',
                        },
                        edge_attr={
                            'fontname': 'Courier',
                        })

        title = "{} - {}\n\n".format(self.xcode_project.name, title)
        graph.attr(label=title)

        graph.attr(labelloc='t')
        graph.attr(fontsize='26')
        graph.attr(rankdir='BT')

        if including_types:
            targets = {t for t in self.xcode_project.targets if t.type in including_types}
        else:
            targets = self.xcode_project.targets

        # Sort nodes by name
        targets = sorted(targets, key=lambda t: t.name)

        # Add nodes
        for xcode_target in targets:
            if xcode_target.type in {XcTarget.Type.TEST, XcTarget.Type.UI_TEST}:
                style = 'dotted'
            elif xcode_target.type in {XcTarget.Type.APP_EXTENSION, XcTarget.Type.WATCH_EXTENSION}:
                style = 'dashed'
            elif xcode_target.type in {XcTarget.Type.APPLICATION, XcTarget.Type.WATCH_APPLICATION}:
                style = 'diagonals'
            else:
                style = 'solid'
            graph.node(xcode_target.name, style=style)

        # Add edges
        for xcode_target in targets:
            dependencies_target = sorted(xcode_target.dependencies, key=lambda t: t.name)  # Sort dependencies by name
            for dependency_target in dependencies_target:
                if including_types and dependency_target.type not in including_types:
                    continue

                graph.edge(xcode_target.name, dependency_target.name)

        graph.render(cleanup=True, view=preview)

        if display_graph_source:
            print(graph.source)

        return True


class XcProjReporter():

    def __init__(self, xcode_project):
        self.xcode_project = xcode_project

    def _print_horizontal_line(self):
        print('--------------------')

    def print_targets(self, by_type=True):
        if not by_type:
            target_names = [t.name for t in self.xcode_project.targets]
            target_names.sort()
            for target_name in target_names:
                print(target_name)
        else:
            self.target_type_counts = dict()

            for target_type in XcTarget.Type.AVAILABLES:
                targets = self.xcode_project.targets_of_type(target_type)

                if not targets:
                    self.target_type_counts[target_type] = (None, len(targets))
                    continue

                # Target type
                target_type_display = '{}s'.format(target_type.replace('_', ' ').capitalize())
                cprint('{} ({}):'.format(target_type_display, len(targets)), attrs=['bold'])

                # Targets
                for target in targets:
                    print('- {}'.format(target.name))
                
                self.target_type_counts[target_type] = (target_type_display, len(targets))
    
    def print_targets_summary(self):
        # Targets summary
        self._print_horizontal_line()

        for target_type in XcTarget.Type.AVAILABLES:
            if self.target_type_counts[target_type][1]:
                print('{:>2} {}'.format(self.target_type_counts[target_type][1],
                                        self.target_type_counts[target_type][0]))
        cprint('{:>2} Targets in total'.format(len(self.xcode_project.targets)), attrs=['bold'])

    def print_files_by_targets(self):
        for target in self.xcode_project.targets_sorted_by_name:
            counters = [
                '{} source files'.format(len(target.source_files)),
                '{} resource files'.format(len(target.resource_files)),
            ]
            target_display = '{} [{}]:'.format(target.name, ', '.join(counters))
            cprint(target_display, attrs=['bold'])

            # Resource and source files of the target
            files = list(target.source_files) + list(target.resource_files)
            filepaths = [f.path for f in files]
            filepaths.sort()
            for filepath in filepaths:
                print(filepath)
    
    def print_files_summary(self):
        self._print_horizontal_line()

        source_files = set()
        resource_files = set()

        for target in self.xcode_project.targets:
            source_files |= target.source_files
            resource_files |= target.resource_files

        source_files_count = len(source_files)
        resource_files_count = len(resource_files)

        total_files_count = source_files_count + resource_files_count

        print('{:>2} Source files in total'.format(source_files_count))
        print('{:>2} Resource files in total'.format(resource_files_count))
        cprint('{:>2} Files in total'.format(total_files_count), attrs=['bold'])
    
    def print_groups(self, filter_empty=False):
        for group_path in self.xcode_project.group_paths(filter_empty=filter_empty):
            print(group_path)