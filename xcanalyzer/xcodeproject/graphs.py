from graphviz import Digraph

from .models import XcTarget


class XcProjectGraphGenerator():

    def __init__(self, xcode_project):
        self.xcode_project = xcode_project
    
    def generate_targets_dependencies_graph(self,
                                            output_format='pdf',  # 'pdf' or 'png'
                                            dependency_type=None,  # 'build' or 'framework'
                                            preview=False,
                                            display_graph_source=False,
                                            filepath=None,
                                            title=None,
                                            including_types=set()):
        if not filepath:
            raise Exception("Missing filepath.")

        if not title:
            raise Exception("Missing title.")
        
        if output_format not in {'pdf', 'png'}:
            raise Exception("Bad output_format '{}'. Only 'pdf' and 'png' are supported.".format(output_format))
        
        if dependency_type not in {'build', 'linked', 'embed'}:
            raise Exception("Bad dependency_type '{}'. Only 'build', 'linked' and 'embed' are supported.".format(dependency_type))

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

        # Target nodes
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

        # Dependencies edges
        for xcode_target in targets:
            if dependency_type == 'build':
                dependencies = xcode_target.dependencies
            elif dependency_type == 'linked':
                dependencies = xcode_target.linked_frameworks
            elif dependency_type == 'embed':
                dependencies = xcode_target.embed_frameworks
            else:
                raise Exception("Dependency type '{}' not supported.".format(dependency_type))

            dependencies_target = sorted(dependencies, key=lambda t: t.name)  # Sort dependencies by name
            for dependency_target in dependencies_target:
                if including_types and dependency_target.type not in including_types:
                    continue

                graph.edge(xcode_target.name, dependency_target.name)

        # Render the graph
        graph.render(cleanup=True, view=preview)

        # Display graph source if asked
        if display_graph_source:
            print(graph.source)

        return True
